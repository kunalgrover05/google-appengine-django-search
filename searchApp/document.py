from google.appengine.api import search
from models import IndexModel
from index import siteIndex
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import urllib

def my_view(request):
    index_create()
    index_delete()

    return HttpResponse('<h1>Page was found</h1>')

def index_create():

    for model in siteIndex.registry:
        rank = siteIndex.ranks[model]
        fields_map = siteIndex.cached_fields[model]
        all_objs = IndexModel.objects.filter(deleted=False)\
                   .filter(processed=False).filter(content_type=ContentType.objects.get(model=model))\
                   .all()[0:150]
        
        docs = []
        index = search.Index(name=model)
        
        for obj in all_objs:
            docs.append(index_document(obj, fields_map, index, rank))
        
        index.put(docs)

def index_delete():
    for model in siteIndex.registry:
        fields_map = siteIndex.cached_fields[model]
        objs = IndexModel.objects.filter(deleted=True)\
               .filter(processed=False).filter(content_type=ContentType.objects.get(model=model))\
               .all()[0:150]
        docs = []
        index = search.Index(name=model)
        for o in objs:
            o.processed = True
            o.save()
            docs.append(str(o.pk))

        index.delete(docs)

def index_document(obj, fields_map, index, rank):
    o = obj.content_object
    search_fields = []

    def get_field(i, f):
        if '.' in f:
            field_split = f.split('.', 1)
            v = getattr(i, field_split[0])
            return get_field(v, field_split[1])
        else:
            return getattr(i, f)
      
    for field_name, field_type in fields_map.iteritems():
        # Make it work for foreign keys
        field_value = get_field(o, field_name)
        
        if field_value.__class__.__name__ == 'ManyRelatedManager':
            # If the value is a Many to Many class, simply take the string representation
            # of the instance
            for f in value.all():
                search_fields += [search.TextField(name=field_name, value=str(f))]

        else:
            search_fields += [field_type(name=field_name.replace('.', '_'), value=field_value)]


    # ALways delete by overwriting
    doc_original = index.get(str(o.pk))

    doc = search.Document(
        doc_id=str(obj.pk),
        fields=search_fields,
        rank=getattr(o, rank)()
    )

    obj.processed = True
    obj.save()
    return doc


# Search service. You can choose to search with a single type or all types
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

