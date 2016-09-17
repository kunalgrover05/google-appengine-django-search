from django.contrib import admin

from .models import Book, Author, BookAdmin, AuthorAdmin, Company, CompanyAdmin

admin.site.register(Book, BookAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Company, CompanyAdmin)
