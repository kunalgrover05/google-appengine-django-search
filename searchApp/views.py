from .forms import SearchForm
from django.shortcuts import render
from google.appengine.api import search
from index import siteIndex
from document import search_index

# Search service View
def search_service(request):
    form = SearchForm(request.GET)
    if form.is_valid():
        index_name = request.GET.get('search_type')
        limit = int(request.GET.get('start', 0)) + int(request.GET.get('end', 5))
        offset = int(request.GET.get('start', 0))

        sort_opts = search.SortOptions(match_scorer=search.MatchScorer())
        query_options = search.QueryOptions(limit=limit, offset=offset, sort_options=sort_opts)
        query_string = request.GET.get('query', "").replace('\'', '')
        response = search_index(index_name, query_string, query_options)

        # Small functionality to get the result that can easily be put in
        # a table. Arranged as set of rows
        headers = siteIndex.registry[index_name].cached_fields.keys() + ['rank']
        result = []
        for r in response:
            output = []
            for k in headers:
                output.append(r.get(k))
            result.append(output)

        return render(request, 'table.html', {'result': result, 'headers': headers })

    form = SearchForm()
    return render(request, 'search.html', {'form': form})