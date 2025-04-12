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



def home(request):
    # render the home page
    return render(request, "home.html")

@login_required(login_url="/login/")
def update(request):
    project = Data.objects.last().get_all_field_values() # TODO change to something more robust

    for field in project:
        print(field)
        if field == "project_id":
            project[field]['value'] += 1 # iterate by 1 # TODO again change to something more robust
        else:
            project[field]['value'] = ""

    return render(request, "input.html", {"project": project})

@login_required(login_url="/login/")
def save_data(request):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("input")

    post_data = request.POST.copy()
    project_id = post_data.get("project_id")

    if not project_id:
        messages.error(request, "Missing project ID.")
        return redirect("input")

    try:
        project_id = int(project_id)
    except ValueError:
        messages.error(request, "Invalid project ID.")
        return redirect("input")
    
    try:
        creation = False
        data_instance = Data.objects.get(project_id=project_id)
    except:
        creation = True
        # we are creating a new field
        data_instance = Data()
        data_instance.project_id = project_id
        data_instance.save()

    # Remove project_id from POST so it doesn’t get processed as a DataField
    post_data.pop("project_id")

    for key, raw_value in post_data.items():

        # Try to match the key to a DataField.verbose_name
        try:
            field = DataField.objects.get(verbose_name=key, archived=False)
        except DataField.DoesNotExist:
            continue  # Silently skip unknown fields

        # Convert the raw_value to the appropriate type
        # TODO add validation checks
        # Create or update DataFieldValue
        if creation:
            field_value = DataFieldValue(data=data_instance, field=field)
        else:
            field_value = DataFieldValue.objects.get(data=data_instance, field=field)
        field_value.value = raw_value
        field_value.save()

        # Ensure the ManyToMany relation is up to date
        data_instance.field_values.add(field_value)

    data_instance.save()
    messages.success(request, "Saved data successfully!")
    return redirect(f"/view/{project_id}")

@login_required(login_url="/login/")
def delete_data(request):
    if request.method == "POST":
        project_id = request.POST.get("project_id")
        if not project_id:
            messages.error(request, "No project ID provided.")
            return redirect("input")

        try:
            obj = get_object_or_404(Data, project_id=project_id)
            obj.delete()
            messages.success(request, f"Project {project_id} deleted successfully.")
        except Exception as e:
            messages.error(request, f"Error deleting project: {e}")

    return redirect("search")


@login_required(login_url="/login/")
def search_data(request):
    project_objs = Data.objects.all().order_by('-created_at')  # Optional: order newest first
    project_objs = [project_obj.get_all_field_values(by_dict=False) for project_obj in project_objs]
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