from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import Http404
from pathlib import Path
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from app.models import Project, DataField, DataFieldValue
from django.shortcuts import get_object_or_404


BASE_DIR = Path(__file__).resolve().parent.parent



def home(request):
    # render the home page
    return render(request, "home.html")

@login_required(login_url="/login/")
def update(request):
    project = Project.objects.last().get_all_field_values() # TODO change to something more robust

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
        data_instance = Project.objects.get(project_id=project_id)
    except:
        creation = True
        # we are creating a new field
        data_instance = Project()
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
            obj = get_object_or_404(Project, project_id=project_id)
            obj.delete()
            messages.success(request, f"Project {project_id} deleted successfully.")
        except Exception as e:
            messages.error(request, f"Error deleting project: {e}")

    return redirect("search")


@login_required(login_url="/login/")
def search_data(request):
    project_queryset = Project.objects.all().order_by('-created_at')
    # Paginate before any heavy processing
    paginator = Paginator(project_queryset, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Now apply get_all_field_values only to items on the current page
    page_obj.object_list = [obj.get_all_field_values(by_dict=False) for obj in page_obj.object_list]

    return render(request, "search_data.html", {"page_obj": page_obj})

@login_required(login_url="/login/")
def view_data(request, project_id):
    project_obj = Project.objects.filter(project_id=project_id)
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