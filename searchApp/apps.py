import webapp2
from django.apps import AppConfig

class DefaultPage(webapp2.RequestHandler):
    """Render empty page when Django setup isn't complete 
       otherwise Apps Not Ready error is thrown."""
    def get(self):
        self.response.out.write('<html><body><h1>Page not loaded</h1></body></html>')

app = webapp2.WSGIApplication([('/index', DefaultPage)], debug=True)

class IndexPage(webapp2.RequestHandler):
    """This indexer is set up only after Django is loaded, see MyAppConfig""" 
    def get(self):
        import document
        document.index_create()
        document.index_delete()
        self.response.out.write('<html><body><h1>Page loaded</h1></body></html>')

class MyAppConfig(AppConfig):
    name = "searchApp"
    def ready(self):
        """Ready to bind the indexer to the URL"""
        global app
        app = webapp2.WSGIApplication([('/index', IndexPage)], debug=True)