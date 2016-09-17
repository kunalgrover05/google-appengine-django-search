from google.appengine.api import search
from models import IndexModel
from index import siteIndex
from django.contrib.contenttypes.models import ContentType


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
            # If the value is a Many to Many class, simply take the space separated
            # string representation of the instances
            search_fields += [search.TextField(name=field_name, value=' '.join(str(x) for x in field_value.all()))]
        else:
            search_fields += [field_type(name=field_name.replace('.', '_'), value=field_value)]

    def get_rank():
        if rank is None:
            return 0
        else:
            return getattr(content_obj, rank)()

    # We can't update, we just overwrite always 
    doc = search.Document(
        doc_id=str(obj.pk),
        fields=search_fields,
        rank=get_rank()
    )

    obj.processed = True
    obj.save()
    return doc


def search_index(index_name, query_string, query_options):
    """
    Search an index and get list of results
    :param index_name: Name of the class
    :param query_string: Query string to search for
    :param query_options
    :return: List of results
    """
    index = search.Index(name=index_name)
    try:
        search_results = index.search(search.Query(query_string=query_string, options=query_options))
    except search.Error:
        search_results = []

    # Serialize and return result
    # Create table from all the data that we had
    response = []
    for result in search_results:
        search_out = {}
        for f in result.fields:
            key = f.name.replace('_', '.')
            value = f.value
            search_out[key] = value
        search_out['rank'] = result.rank
        response.append(search_out)
    return response
