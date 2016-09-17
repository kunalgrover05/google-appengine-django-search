from django.apps import AppConfig
import django.dispatch

class MyAppConfig(AppConfig):
    name = "testApp"
    def ready(self):
    	# Should be called only when Apps are initialized
        from searchApp.index import siteIndex
        from .models import Book
		
        siteIndex.register(Book,
            ['name', 'description', 'date', 'author.name', 'author.publisher.name', 'tags'],
            'getScore')
