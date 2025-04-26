from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import HttpResponse
from app.models import Project, DataField, DataFieldValue
from django.shortcuts import get_object_or_404
import pandas as pd
import os
import tempfile
from datetime import timedelta

def validate_superuser(request):
    try:
        return request.user.is_superuser and request.user.is_authenticated
    except:
        pass
    return False

@login_required(login_url="/login/")
def custom_admin(request):
    if not validate_superuser(request):
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
                field.delete() # then delete the field 
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
            for data_instance in Project.objects.all():
                data_instance.field_values.create(field=new_field, value=None)
                data_instance.save()

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


# Function to handle timedelta conversion
def convert_to_serializable(value):
    if isinstance(value, str):
        if " mins" in value:
            value = value.replace(" mins", " minutes")
        if "nan" == value:
            value = ""
    
    if isinstance(value, timedelta):
        # Convert timedelta to total seconds (or any other representation you prefer)
        days = value.days
        # Get total seconds and calculate hours and minutes
        hours, remainder = divmod(value.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        # Build the output string
        result = []
        if days > 0:
            result.append(f"{days} days")
        if hours > 0:
            result.append(f"{hours} hours")
        if minutes > 0:
            result.append(f"{minutes} minutes")
        
        # Handle the case where all values are 0
        if not result:
            return "0 minutes"
        return " ".join(result)
    return value




from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import pandas as pd
import tempfile
import os

@login_required(login_url="/login/")
def analyze_file(request):
    if not request.user.is_superuser:
        return redirect("logout")

    if request.method == 'POST' and 'data_file' in request.FILES:
        uploaded_file = request.FILES['data_file']
        temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)

        with open(temp_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)


            # Load file into pandas
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(temp_path)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(temp_path)
            else:
                return render(request, 'custom_admin/analyze.html', {
                    'error': 'Unsupported file type.'
                })

            df.fillna(value="nan", inplace=True)
            columns = df.columns.tolist()
            rows = df.values.tolist()
            readout = ""

            # Column -> DataField mapping
            accepted_fields = list(DataField.objects.all())
            col_assoc = {}
            for i in range(len(columns)):
                column = columns[i]
                if column not in ['nan']:
                    is_bad = True
                    for field in accepted_fields:
                        if field.check_reduced(column):
                            col_assoc[column] = field
                            is_bad = False
                    print("bad", is_bad, column)
            print(col_assoc)
            project_ids = [row[0] for row in rows]

            # Delete old projects
            old_projects = list(Project.objects.filter(project_id__in=project_ids))
            deleted_map = {p.project_id for p in old_projects}
            if old_projects:
                Project.objects.filter(id__in=[p.id for p in old_projects]).delete()
                readout += f"Deleted {len(deleted_map)} existing projects.<br>"

            # Create new projects
            Project.objects.bulk_create([Project(project_id=pid) for pid in project_ids])

            # Re-fetch projects (bulk_create doesn't return instances with IDs)
            projects = {
                p.project_id: p for p in Project.objects.filter(project_id__in=project_ids)
            }

            # Build DataFieldValue objects
            all_values = []
            project_to_values = {pid: [] for pid in project_ids}

            for j, row in enumerate(rows):
                project_id = row[0]
                project = projects.get(project_id)
                if not project:
                    continue

                if project_id in deleted_map:
                    readout += f"<b>Created project {project_id}</b><br>"

                for i, column in enumerate(columns):
                    if column in col_assoc:
                        field = col_assoc[column]
                        value = convert_to_serializable(row[i])
                        dfv = DataFieldValue(data=project, field=field, value=value)
                        all_values.append(dfv)
                        project_to_values[project_id].append(dfv)

            # Save all field values
            DataFieldValue.objects.bulk_create(all_values)

            # Set reverse M2M
            for pid, values in project_to_values.items():
                project = projects[pid]
                project.field_values.set(values)

            return render(request, 'custom_admin/analyze.html', {
                'analysis': 'Successfully saved!',
                'readout': f'Readout: {readout}'
            })


    return render(request, 'custom_admin/analyze.html', {
        'error': 'No file uploaded.'
    })
