from django.apps import AppConfig
import django.dispatch
deleted_signal = django.dispatch.Signal()

class MyAppConfig(AppConfig):
    name = "test"
    def ready(self):
        from searchApp.index import siteIndex
        from .models import Book
		

        siteIndex.register(Book, ['name', 'description', 'date', 'author.name', 'author.company.company'], 
        	'getScore',
        	 deleteSignal=deleted_signal)

