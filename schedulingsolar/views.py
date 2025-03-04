from django.shortcuts import render, HttpResponse

def new_page(request):
    return HttpResponse("This is a new page")


def home(request):
    return render(request, "home.html")


def page_not_found(request, error_msg):
    return HttpResponse(error_msg)