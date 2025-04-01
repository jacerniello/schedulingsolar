from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import Http404, JsonResponse
from django.core.exceptions import ValidationError
from pathlib import Path
import json
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import Data

BASE_DIR = Path(__file__).resolve().parent.parent


def home(request):
    # render the home page
    return render(request, "home.html")

@login_required(login_url="/login/")
def update(request):
    print(BASE_DIR / "schedulingsolar/app/static/json/features.json")
    features = json.load(open(BASE_DIR / "app/static/json/features.json", "r"))

    return render(request, "input.html", {"features": features})

@login_required(login_url="/login/")
def save_data(request):
    if request.method == "POST":
        data = request.POST

        named_attrs = {field.name: field for field in Data._meta.fields}  # Store fields with types

        obj = Data()
        for key, value in data.items():
            if isinstance(value, str) and len(value) == 0: continue
            if key in named_attrs:
                field = named_attrs[key]
                
                # Validate data type (if the data is an invalid type, raise this error)
                # TODO make sure that the input form has validation so this doesn't need to be run
                expected_type = field.get_internal_type()
                if expected_type in ["IntegerField", "BigIntegerField"] and not isinstance(value, int):
                    raise ValidationError(f"Expected an integer for {key}, but got {type(value).__name__}")
                elif expected_type in ["FloatField", "DecimalField"] and not isinstance(value, (float, int)):
                    raise ValidationError(f"Expected a float/decimal for {key}, but got {type(value).__name__}")
                elif expected_type == "BooleanField" and not isinstance(value, bool):
                    raise ValidationError(f"Expected a boolean for {key}, but got {type(value).__name__}")
                elif expected_type in ["CharField", "TextField"] and not isinstance(value, str):
                    raise ValidationError(f"Expected a string for {key}, but got {type(value).__name__}")

                setattr(obj, key, value)

        obj.save()
        
        messages.success(request, "Saved data successfully!")
    else:
        messages.error(request, "Not a valid input type")

    return redirect("input")

@login_required(login_url="/login/")
def view_data(request):
    return render(request, "view_data.html")

@login_required(login_url="/login/")
def edit_data(request):
    return render(request, "edit.html")


def page_not_found(request, error_msg):
    raise Http404("Page not found")



### LOGIN/LOGOUT ###

def login_view(request):
    # to render a template
    # render(request, "login.html")
    if request.method == "GET":
        return render(request, "login.html")
    elif request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        print(username, password)
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect to a success page.
            messages.success(request, "You successfully logged in!")
            return redirect("home")
        else:
            return HttpResponse("Incorrect login, try again.")


@login_required(login_url="/login/")
def logout_view(request):
    logout(request)
    messages.success(request, "You successfully logged out!")
    return redirect("home")