from django.shortcuts import render
from django.views.generic import ListView


class AboutListView(ListView):
    template = 'pages/about.html'


class RulesListView(ListView):
    template = 'pages/rules.html'


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)


def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def handler500(request):
    return render(request, 'pages/500.html', status=500)
