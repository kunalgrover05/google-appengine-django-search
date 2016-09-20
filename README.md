# google-appengine-django-search
Module for automatically easily setting up Google App Engine Search with Django, with minimal configuarion. https://cloud.google.com/appengine/docs/python/search/

The app maintains a table that is used to keep the state of documents on Google App Engine's Document API. It is highly recommended to use the default cron based functionality to do batch updates periodically(See USAGE for details). By default, the updates on the Search documents are not instant and depend on the period of the cron service.

## Features:
- Link multiple models as different search namespaces and can search any of them
- Automatically listens to post_save and post_delete signals to update the search documents.
- Support for ForeignKey and ManyToMany fields, Custom update listener and override for post_delete signal.
- Supports App Engine Search API queries directly.
- Ability to rank documents based on priority.
- Google App Engine compatible cron service for automatically updating documents on update periodically.

## Configuration:
* Install by adding searchApp to INSTALLED_APPS in settings.py
* Bind to model using apps.py
models.py
```
class ModelName(models.Model):
    field = models.CharField()
    foreignKey = models.ForeignKey(OtherModel)
    manyToManyField = models.ManyToManyField(DifferentModel)
    
    def rankGetter(self):
        return self.rank
```

Example apps.py setup
```
  class MyAppConfig(AppConfig):
      name = "appName"
      def ready(self):
          from searchApp.index import siteIndex
          from .models import ModelName
          siteIndex.register(ModelName,
              ['field', 'foreignKey.field', 'manyToManyField'], 'rankGetter', html_fields=['field'],
              deleteSignal=customDeleteSignal, updateSignal=customUpdateSignal)
```
* Setup cron service. 
Add to app.yaml under handlers
```
handlers:
- url: /index
  script: searchApp.apps.app
```
And this to cron.yaml with a desired update frequency. https://cloud.google.com/appengine/docs/python/config/cron
```
cron:
- description: Index ranking
  url: /index
  schedule: every 5 minutes
```
* That's it! Ready to use search service!

#### Note:   
- The html_fields attribute represents a list of fields where searching should ignore the HTML tags. Helpful if you allow users to save HTML in text fields.
- Custom signals can be added using https://docs.djangoproject.com/en/1.10/topics/signals/#defining-and-sending-signals
- The deleteSignal can be used if using Soft deletes(ie not deleting from the database by setting some field). 
- The updateSignal is helpful when Foreign key dependencies are updated. Currently, the update will be done using post_save which will cause missed updates in dependencies.

## Usage
- Start dev_appserver.py and run [http://localhost:8080/index](http://localhost:8080/index) to update the search documents. If the response says "Page not loaded" it means that Django is not initialized completely yet, and you need to open some Django URL for that to happen. "Page loaded" means that Django is working correctly.
- Open [http://localhost:8080/search](http://localhost:8080/search) and make your searches.

### Manually updating search documents(Not recommended as it might slow down your application)
You can use index_create_single(obj) and index_delete_single(obj) from searchApp.document

### Get results from Search API
Use search_index(index_name, query_string, query_options) from searchApp.document, see searchApp.views for example implementation.

### Search API examples to test out in testApp
- [tags: Horror NOT tags: Romance] (https://django-test-143704.appspot.com/search?search_type=Book&query=tags%3A+Horror+NOT+tags%3A+Romance&start=0&end=5)
- [date < 2005-04-01] (https://django-test-143704.appspot.com/search?search_type=Book&query=date+%3C+2005-04-01&start=0&end=5)
- [description: novel] (https://django-test-143704.appspot.com/search?search_type=Book&query=description%3A+novel&start=0&end=5)
- [author_name=Jean] (https://django-test-143704.appspot.com/search?search_type=Book&query=author_name%3A+Jean&start=0&end=5)
- [author_publisher_name=Atlas Press] (https://django-test-143704.appspot.com/search?search_type=Book&query=author_publisher_name%3A+Atlas+Press&start=0&end=5)
