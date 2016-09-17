from django import forms
from index import siteIndex


class SearchForm(forms.Form):
    choices = tuple(siteIndex.registry.keys())
    search_type = forms.ChoiceField(label='Search Type', choices=[(k, k) for k in siteIndex.registry.keys()])
    query = forms.CharField(label='Query')
    start = forms.IntegerField(label='Start', initial=0)
    end = forms.IntegerField(label='End', initial=5)