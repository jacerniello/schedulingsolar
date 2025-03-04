from django.shortcuts import render, HttpResponse
from django.http import Http404

def new_page(request):
    return HttpResponse("This is a new page")


def home(request):
    return render(request, "home.html")


def page_not_found(request, error_msg):
    raise Http404("Page not found")