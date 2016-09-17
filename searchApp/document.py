from google.appengine.api import search
from models import IndexModel
from index import siteIndex
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import urllib

def index_create_single(instance):
    """Call this function for manually updating a single document, 
       not recommended"""
    model = instance.__class__.__name__
    searchObj = siteIndex.registry.get(model)

    obj = IndexModel.objects.get(content_type=ContentType.objects.get(model=model),
        object_id=instance.pk)

    rank = searchObj.rank
    fields_map = searchObj.cached_fields

    index = search.Index(name=model)
    index.put(index_document(obj, fields_map, rank))

    # Update this model value
    obj.processed = True
    obj.save()

def index_delete_single(instance):
    """Call this function for manually deleting a single document, 
       not recommended"""
    model = instance.__class__.__name__
    searchObj = siteIndex.registry.get(model)

    obj = IndexModel.objects.get(content_type=ContentType.objects.get(model=model),
     object_id=instance.pk)
    
    index = search.Index(name=model)
    index.delete(str(obj.pk))

    # Update this model value
    obj.processed = True
    obj.save()

def index_create():
    """Batch Update Search indexes, preferably not run in request period"""
    for model, searchObj in siteIndex.registry.iteritems():
        rank = searchObj.rank
        fields_map = searchObj.cached_fields
        all_objs = IndexModel.objects.filter(deleted=False)\
                   .filter(processed=False).filter(content_type=ContentType.objects.get(model=model))\
                   .all()[0:150]
        
        docs = []
        index = search.Index(name=model)
        
        for obj in all_objs:
            obj.processed = True
            obj.save()
            docs.append(index_document(obj, fields_map, rank))
        
        index.put(docs)

# Delete Search Indexes
def index_delete():
    """Batch delete Search indexes, preferably not run in request period"""
    for model, searchObj in siteIndex.registry.iteritems():
        fields_map = searchObj.cached_fields
        all_objs = IndexModel.objects.filter(deleted=True)\
               .filter(processed=False).filter(content_type=ContentType.objects.get(model=model))\
               .all()[0:150]
        
        docs = []
        index = search.Index(name=model)
        
        for obj in all_objs:
            index_delete_single(obj.content_object)

            obj.processed = True
            obj.save()
            # Deleting requires just list of document IDs
            docs.append(str(obj.pk))

        index.delete(docs)

# Index a document with the given data
def index_document(obj, fields_map, rank):
    content_obj = obj.content_object
    search_fields = []

    def get_field(i, f):
        # Magic function!! Traverses down foreign key
        # relationships
        if '.' in f:
            field_split = f.split('.', 1)
            v = getattr(i, field_split[0])
            return get_field(v, field_split[1])
        else:
            return getattr(i, f)
      
    for field_name, field_type in fields_map.iteritems():
        field_value = get_field(content_obj, field_name)
        
        if field_value.__class__.__name__ == 'ManyRelatedManager':
            # If the value is a Many to Many class, simply take the string representation
            # of the instance
            for f in field_value.all():
                search_fields += [search.TextField(name=field_name, value=str(f))]

        else:
            search_fields += [field_type(name=field_name.replace('.', '_'), value=field_value)]

    def get_rank():
        if rank is None:
            return 0
        else:
            return getattr(o, rank)() 

    # We can't update, we just overwrite always 
    doc = search.Document(
        doc_id=str(obj.pk),
        fields=search_fields,
        rank=get_rank()
    )

    obj.processed = True
    obj.save()
    return doc

# Search service View
def search_service(request):
    index_name = request.GET.get('type', 'Book')
    limit = int(request.GET.get('start', 0)) + int(request.GET.get('end', 5))
    offset = request.GET.get('start', 0)

    search_results = {}

    sort_opts = search.SortOptions(match_scorer=search.MatchScorer())
    query_options = search.QueryOptions(limit=limit, offset=offset, sort_options=sort_opts)

    index = search.Index(name=index_name)
    query_string = request.GET.get('query', "").replace('\'', '')

    try:
        values = []
        search_results = index.search(search.Query(query_string=query_string, options=query_options))

    except search.Error:
        search_results = []

    # Serialize and return result
    return JsonResponse(search_results, safe=False)

