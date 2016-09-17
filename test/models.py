from django.db import models
import datetime
from django.contrib import admin
from django.dispatch import receiver

class Company(models.Model):
	company = models.IntegerField()

class Author(models.Model):
	name = models.CharField(max_length=100)
	age = models.IntegerField()
	company = models.ForeignKey(Company)
	def __unicode__(self):
		return u'%s' % (self.name)

class Book(models.Model):
	name = models.CharField(max_length=100)
	author = models.ForeignKey(Author)
	description = models.TextField()
	date = models.DateField(default=datetime.date.today)
	likes = models.IntegerField()

	def getScore(self):
		return self.likes

	def __unicode__(self):
		return u'%s' % (self.name)


class CompanyAdmin(admin.ModelAdmin):
	list_display = (('company', ))

class AuthorAdmin(admin.ModelAdmin):
	list_display = (('name', ))

class BookAdmin(admin.ModelAdmin):
	list_display = (('name', ))

