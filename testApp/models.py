from django.db import models
from django.contrib import admin
from django.dispatch import receiver

##########################################################

class Publisher(models.Model):
	name = models.CharField(max_length=100)
	
	def __unicode__(self):
		return u'%s' % (self.name)

class PublisherAdmin(admin.ModelAdmin):
	list_display = (('name', ))

##########################################################

class Tag(models.Model):
	name = models.CharField(max_length=100, primary_key=True)
	
	def __unicode__(self):
		return u'%s' % (self.name)

class TagAdmin(admin.ModelAdmin):
	list_display = (('name', ))

##########################################################

class Author(models.Model):
	name = models.CharField(max_length=100)
	age = models.IntegerField()
	publisher = models.ForeignKey(Publisher)

	def __unicode__(self):
		return u'%s' % (self.name)

class AuthorAdmin(admin.ModelAdmin):
	list_display = (('name', 'publisher'))

##########################################################

class Book(models.Model):
	name = models.CharField(max_length=100)
	author = models.ForeignKey(Author)
	description = models.TextField()
	date = models.DateField()
	likes = models.IntegerField()
	tags = models.ManyToManyField(Tag)

	# Ranking setup for search results
	def getScore(self):
		return self.likes

	def __unicode__(self):
		return u'%s' % (self.name)

class BookAdmin(admin.ModelAdmin):
	list_display = (('name', ))

##########################################################

# Register model with admin
admin.site.register(Book, BookAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Publisher, PublisherAdmin)

##########################################################

# Example setup
# publisher = Publisher.objects.create(name="McGill Publisher")
# author = Author.objects.create(publisher=publisher, name="")







