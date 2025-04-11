from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import Http404, JsonResponse
from django.core.exceptions import ValidationError
from pathlib import Path
import json
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from app.models import Data, DataField, DataFieldValue
from django.shortcuts import get_object_or_404
#from app.models import Data
from django.core.files.storage import FileSystemStorage
import pandas as pd
import os
import tempfile
from .train import *

# TODO FIX THE analyze_file method
# for now just get the data in manually

BASE_DIR = Path(__file__).resolve().parent.parent
features = json.load(open(BASE_DIR / "app/static/json/features.json", "r"))



def home(request):
    # render the home page
    return render(request, "home.html")

@login_required(login_url="/login/")
def update(request):
    print(BASE_DIR / "schedulingsolar/app/static/json/features.json")
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
def search_data(request):
    project_objs = Data.objects.all().order_by('-created_at')  # Optional: order newest first
    project_objs = [project_obj.get_all_field_values() for project_obj in project_objs]
    print(project_objs[0])
    if len(project_objs) == 0:
        return render(request, "search_data.html", {"page_obj": []})
    paginator = Paginator(project_objs, 6)  # Show 6 projects per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "search_data.html", {"page_obj": page_obj})

@login_required(login_url="/login/")
def view_data(request, project_id):
    project_obj = Data.objects.filter(project_id=project_id)
    if not project_obj:
        messages.error(request, "Not a valid Project ID")
        return redirect("home")

    return render(request, "view_data.html", {"project": project_obj.first().get_all_field_values(), 
                                              "header": "View/Edit Data"})


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
        else:
            messages.error(request, "Incorrect login, try again.")
            return redirect("login")
        return redirect("home")


@login_required(login_url="/login/")
def logout_view(request):
    logout(request)
    messages.success(request, "You successfully logged out!")
    return redirect("home")


### Custom Admin ###

def validate_superuser(request):
    try:
        return request.user.is_superuser and request.user.is_authenticated
    except:
        pass
    return False

@login_required(login_url="/login/")
def custom_admin(request):
    if not validate_superuser:
        return redirect("logout")
    return render(request, "custom_admin/custom_admin.html")



@login_required(login_url="/login/")
def save_input_field(request):
    """all logic for input fields"""

    if not validate_superuser:
        # make sure it is super user
        return redirect("logout")

    if request.method == 'POST':
        # actually save change to database
        field_name = request.POST.get('new_field_name', '')
        field_type = request.POST.get('new_field_type', '')
        field_choices = request.POST.get('new_field_choices', '')

        # in case of existing field
        field_id = request.POST.get('field_id', '')
        delete_field = request.POST.get('delete_field', False)
        if field_id:
            # we are editing existing field
            try:
                field = DataField.objects.get(id=field_id)
            except:
                messages.error(request, "Could not find the field by id")
                return redirect('save_input_field')
            if not field:
                # same error
                messages.error(request, "Could not find the field by id")
                return redirect('save_input_field')
            
            if delete_field:
                field.delete()
                messages.success(request, "Deleted the field")
                return redirect('save_input_field')
            else:
                # do not delete, must want to edit
                field.verbose_name = field_name
                field.field_type = field_type
                field.choices =[x.strip() for x in field_choices.split(',')] if field_type == 'choice' else ['']
                field.save() # save the updated field
                messages.success(request, "Updated the field")
                return redirect('save_input_field')
        else:
            # Basic validation for required fields
            if not field_name or not field_type:
                messages.error(request, "Field name and field type are required.")
                return redirect('save_input_field')

            if field_type == 'choice' and not field_choices:
                messages.error(request, "Choices are required for 'Choice' fields.")
                return redirect('save_input_field')
        
            # Create the new field
            new_field = DataField.objects.create(
                verbose_name=field_name,
                field_type=field_type,
                choices=[x.strip() for x in field_choices.split(',')] if field_type == 'choice' else [''],
            )

            # Link the new field to all existing data instances
            for data_instance in Data.objects.all():
                try:
                    data_instance.field_values.create(field=new_field, value=None)  # Assuming field_values is a related manager
                    data_instance.save()
                except ValidationError as e:
                    messages.error(request, f"Error saving field values: {e}")
                    return redirect('save_input_field')

            messages.success(request, "Field saved and linked to all data instances successfully!")
        return redirect('save_input_field')
    
    elif request.method == 'GET':
        field_id = request.GET.get("field_id", "")
        data_fields = DataField.objects.all()
        if not field_id:
            # create a new field
            return render(request, 'custom_admin/save_input_field.html', {"data_fields": data_fields})
        else:
            # edit an existing field
            if field_id:
                field = get_object_or_404(DataField, id=field_id)
            else:
                field = None

            return render(request, "custom_admin/save_input_field.html", {'data_fields': data_fields, 
                                                                        "field_to_edit": field})


@login_required(login_url="/login/")
def edit_model_type(request):
    if not validate_superuser:
        return redirect("logout")
    return render(request, "custom_admin/edit_model_type.html")


@login_required(login_url="/login/")
def analyze_file(request):
    # TODO FIX FIX FIX FIX FIX!!!!!!!!!!!
    if not validate_superuser:
        return redirect("logout")
    
    if request.method == 'POST' and request.FILES['data_file']:
        uploaded_file = request.FILES['data_file']
        
        # Save to temp dir
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(temp_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Read the file using pandas
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(temp_path)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(temp_path)
            else:
                return render(request, 'analyze.html', {
                    'error': 'Unsupported file type.'
                })
            values = df.values.tolist()
            # TODO FIX, make more resilient
            
            analysis = {
                'num_rows': df.shape[0],
                'num_columns': df.shape[1],
                'columns': list(df.columns),
                'preview': df.head().to_html(classes="table table-striped", index=False)
            }

            return render(request, 'analyze.html', {'analysis': analysis})

        except Exception as e:
            return render(request, 'analyze.html', {'error': str(e)})

    return render(request, 'analyze.html', {'error': 'No file uploaded.'})