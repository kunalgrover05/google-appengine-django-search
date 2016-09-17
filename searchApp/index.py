from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from google.appengine.api import search
from .models import IndexModel
from django.contrib.contenttypes.models import ContentType

class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class InvalidModel(Exception):
    pass

class SearchIndex(object):
    """
    Singleton object to allow registering different models
    """

    @staticmethod
    def getSearchType(fieldType, isHTML):
        MAP = {
            models.fields.DateField: search.DateField,
            models.fields.IntegerField: search.NumberField
        }

        if (isHTML):
            return search.HtmlField

        return MAP.get(fieldType, search.TextField)

    def __init__(self):
        self.registry = {}
        
        # Contains map of fields with types, can be reused easily
        self.fields = {}

        # Map of function to give rank while creating
        self.ranks = {}

        # Cache field types on first time they are used
        self.cached_fields = {}

        self.html_fields = {}


    def signal_handler(self, sender, instance, created, **kwargs):
        """ Signal handler on create and update"""
        self.index(instance)
        
    def signal_delete_handler(self, sender, instance, **kwargs):
        self.delete_index(instance)
        print "Deleted signal working"
        
    def register(self, model, fields, rank, **kwargs):
        """
        Registers the given model class(es).
        If a model is already registered, this will raise AlreadyRegistered.
        If a model is abstract, this will raise ImproperlyConfigured.
        """
        if not issubclass(model, models.Model):
            raise InvalidModel('The model %s is an invalid model' % model.__name__)

        if model._meta.abstract:
            raise ImproperlyConfigured('The model %s is abstract,'
                                       ' so it cannot be registered.' % model.__name__)

        if model in self.registry:
            raise AlreadyRegistered('The model %s is already registered' % model.__name__)

        self.registry[model.__name__] = model
        self.fields[model.__name__] = fields
        self.ranks[model.__name__] = rank
        self.html_fields[model.__name__] = kwargs.get('html_fields', [])

        deleted_signal = kwargs.get('deleteSignal', models.signals.post_delete)
        def get_field(m, f):
            print m, f
            if '.' in f:
                split_field = f.split('.', 1)
                print split_field
                model = m._meta.get_field(split_field[0]).rel.to
                return get_field(model, split_field[1])
            else:
                return m._meta.get_field(f)

        if self.cached_fields.get(model.__name__, None) == None:
            self.cached_fields[model.__name__] = {}

            for field in self.fields[model.__name__]:
                self.cached_fields[model.__name__][field] = SearchIndex.getSearchType(
                    type(get_field(model, field)),
                    field in self.html_fields[model.__name__]
                    )

        print self.cached_fields

        models.signals.post_save.connect(self.signal_handler, weak=False, sender=model)
        deleted_signal.connect(self.signal_delete_handler, weak=False, sender=model)

        
    def index(self, instance):
        """
        Mark instance as to be indexed by the server
        """
        model = self.registry[type(instance).__name__]
        rank_key = self.ranks[type(instance).__name__]
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
        print "In delete index", instance.pk
        try:
            i=IndexModel.objects.get(content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.pk)
        except ObjectDoesNotExist:
            print "Can't find to delete"
            return

        if not i.deleted:
            i.deleted = True
            i.save()

siteIndex = SearchIndex()

