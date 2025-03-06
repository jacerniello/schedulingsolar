from django.shortcuts import render, HttpResponse
from django.http import Http404

def new_page(request):
    return HttpResponse("This is a new page")


def home(request):
    return render(request, "home.html")


def page_not_found(request, error_msg):
    raise Http404("Page not found")

def save(request):
    parameters = request.GET
    response_content = ""
    count = 1
    for key, value in parameters.items():
        if not value:
            value = "NULL"
        response_content += f"({count}) {key}: {value}<br>"
        count += 1
    return HttpResponse(f"This page currently doesn't do anything, sorry :). But here are your input parameters and values: <br><br>{response_content}")