from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from google.appengine.api import search
from .models import IndexModel
from django.contrib.contenttypes.models import ContentType

class SearchObject():
    """The search object which is registered in the
       application- Parameters:
        modelClass: Class to register the model with
        fields: List of fields as ['fieldName', 'foreignKey.fieldName']
            Integer fields are saved as search.NumberField
            Date fields are saved as search.DateField
        rank: Function present in the model Class that gives the rank
            for the particular instance. Should be invokable using 
            getAttr(instance, rank)- Higher is better
        html_fields: List of fields to be treated as search.HTMLField ie
            only the content is searchable after ignoring HTML tags.
        deleteSignal: A signal object that maps the user's soft delete 
            functions instead of using the post_delete signal
        updateSignal: An additional signal object that maps to updates.
            Useful to manually update search database on Foreign Key updates.
       """
    @staticmethod
    def get_field(m, f):
        if '.' in f:
            split_field = f.split('.', 1)
            model = m._meta.get_field(split_field[0]).rel.to
            return SearchObject.get_field(model, split_field[1])
        else:
            return m._meta.get_field(f)

    def __init__(self, modelClass, fields, rank, **kwargs):
        self.model = modelClass
        self.fields = fields
        self.rank = rank
        self.html_fields = kwargs.get('html_fields', None)
        self.cached_fields = {}

        for field in self.fields:
            self.cached_fields[field] = SearchIndex.getSearchType(
                type(SearchObject.get_field(self.model, field)),
                field in self.html_fields)
 

class SearchIndex():
    @staticmethod
    def getSearchType(fieldType, isHTML):
        DATATYPE_MAP = {
            models.fields.DateField: search.DateField,
            models.fields.IntegerField: search.NumberField
        }

        if (isHTML):
            return search.HtmlField

        return DATATYPE_MAP.get(fieldType, search.TextField)

    def __init__(self):
        self.registry = {}

    def signal_handler(self, sender, instance, created, **kwargs):
        """ Signal handler on create and update"""
        self.index(instance)
        
    def signal_delete_handler(self, sender, instance, **kwargs):
        """ Signal handler on delete and update"""
        self.delete_index(instance)
        
    def register(self, model, fields, rank, **kwargs):
        """
        Registers the given model class(es).
        Model shouldn't be abstract or registered privately.
        """
        if not issubclass(model, models.Model):
            raise Exception('The model %s is an invalid model' % model.__name__)

        if model._meta.abstract:
            raise Exception('The model %s is abstract,'
                                       ' so it cannot be registered.' % model.__name__)

        if model in self.registry:
            raise Exception('The model %s is already registered' % model.__name__)

        delete_signal = kwargs.get('deleteSignal', models.signals.post_delete)
        update_signal = kwargs.get('updateSignal', None)
        searchObj = SearchObject(model, fields, rank, html_fields=[])
        self.registry[model.__name__] = searchObj

        models.signals.post_save.connect(self.signal_handler, weak=False, sender=model)
        delete_signal.connect(self.signal_delete_handler, weak=False, sender=model)
        if update_signal:
            update_signal.connect(self.signal_delete_handler, weak=False, sender=model)
        
    def index(self, instance):
        """
        Mark instance as to be indexed by the server
        """
        try:
            i = IndexModel.objects.get(content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.pk)
            if i.processed:
                i.processed = False
                i.save()
        except ObjectDoesNotExist:
            i = IndexModel(content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.pk)
            i.save()

    def delete_index(self, instance):
        """"
        Delete index for an instance
        """
        try:
            i=IndexModel.objects.get(content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.pk)
        except ObjectDoesNotExist:
            return

        if not i.deleted:
            i.deleted = True
            i.save()

siteIndex = SearchIndex()

