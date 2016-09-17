import webapp2
from django.apps import AppConfig

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('<html><body><h1>Page was NOT found</h1></body></html>')

app = webapp2.WSGIApplication([('/index', MainPage)], debug=True)

class SubPage(webapp2.RequestHandler):
    def get(self):
        import document
        document.index_create()
        document.index_delete()
        self.response.out.write('<html><body><h1>Page was found</h1></body></html>')

class MyAppConfig(AppConfig):
    name = "searchApp"
    def ready(self):
        global app
        app = webapp2.WSGIApplication([('/index', SubPage)], debug=True)