from django.db import models
import re

class DataField(models.Model):
    FIELD_TYPE_CHOICES = [
        ("degrees", "Degrees"),
        ("char", "Text"),
        ("int", "Integer"),
        ("float", "Float"),
        ("bool", "Boolean"),
        ("choice", "Choice"),
        ("datetime", "DateTime"),
        # etc.
    ]

    name = models.CharField(max_length=255)
    verbose_name = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    choices = models.JSONField(blank=True, null=True)
    default_value = models.JSONField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def check_reduced(self, a):
        a = re.sub(r'\s+', '', a).lower()
        b = re.sub(r'\s+', '', self.verbose_name).lower()
        return a == b

    def __str__(self):
        return f"{self.verbose_name} ({'Archived' if self.archived else 'Active'})"


class DataFieldValue(models.Model):
    data = models.ForeignKey("Data", on_delete=models.CASCADE, related_name="data_field_values")
    field = models.ForeignKey(DataField, on_delete=models.CASCADE)
    value = models.JSONField()

    def save(self, *args, **kwargs):
        # Prevent saving if field is archived
        if self.field.archived:
            raise ValueError(f"Cannot save value for archived field: {self.field.name}")
        super().save(*args, **kwargs)


class Data(models.Model):
    project_id = models.IntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Change related_name to avoid conflict
    field_values = models.ManyToManyField(DataFieldValue, related_name="data_field_values_reverse")

    def get_active_field_values(self):
        # Only fetch values for non-archived fields
        return self.field_values.filter(field__archived=False)

    def get_field_value(self, field_name):
        try:
            field = DataField.objects.get(name=field_name, archived=False)
            return DataFieldValue.objects.get(data=self, field=field).value
        except DataField.DoesNotExist:
            return None

    def archive_field(self, field_name):
        # Mark the field as archived, but do not delete its data
        try:
            field = DataField.objects.get(name=field_name)
            field.archived = True
            field.save()
        except DataField.DoesNotExist:
            raise ValueError(f"Field '{field_name}' does not exist.")
    
    def get_all_field_values(self, by_dict=True):
        # Fetching values from DataFieldValue (related fields)
        if by_dict:
            related_field_values = {'project_id': {"value": self.project_id, "type": "int"}}
        else:
            related_field_values = {'project_id': self.project_id}
        
        for data_field_value in self.field_values.all():
            field = data_field_value.field
            if not field.archived:  # Ensure we only get active fields
                if by_dict:
                    related_field_values[field.verbose_name] = {"value": data_field_value.value, "type": field.field_type, "options": field.choices}
                else:
                    related_field_values[field.verbose_name] = data_field_value.value
                
        # Combine both direct and related field values
        return related_field_values
    
"""
# old version of model

class Data(models.Model):
    # Fields
    project_id = models.IntegerField(unique=True, verbose_name="Project ID")
    drive_time = models.FloatField(default=-1., verbose_name="Drive Time")
    tilt = models.CharField(default="", max_length=400, verbose_name="Tilt")
    azimuth = models.CharField(default="", max_length=400, verbose_name="Azimuth")
    panel_qty = models.IntegerField(default=1, verbose_name="Panel QTY")
    sys_rating = models.FloatField(default=-1., verbose_name="System Rating (kW DC)")
    inv_manu = models.CharField(max_length=1000, verbose_name="Inverter Manufacturer")
    array_type = models.CharField(max_length=1000, verbose_name="Array Type")
    sqrl_screen = models.BooleanField(default=None, null=True, verbose_name="Squirrel Screen")
    cons_monito = models.BooleanField(default=None, null=True, verbose_name="Consumption Monitoring")
    truss_rafter = models.CharField(max_length=10, verbose_name="Truss / Rafter")
    reinforcements = models.BooleanField(default=None, null=True, verbose_name="Reinforcements")
    elec_inspec = models.BooleanField(default=None, null=True, verbose_name="Rough Electrical Inspection")
    intercon_type = models.CharField(max_length=1000, verbose_name="Interconnection Type")
    module_len = models.FloatField(default=-1., verbose_name="Module Length")
    module_width = models.FloatField(default=-1., verbose_name="Module Width")
    module_weight = models.FloatField(default=-1., verbose_name="Module Weight")
    array_num = models.FloatField(default=-1., verbose_name="# of Arrays")
    reinforcement_num = models.FloatField(default=-1., verbose_name="# of Reinforcement")
    roof_type = models.CharField(max_length=200, verbose_name="Roof Type")
    attach_type = models.CharField(max_length=200, verbose_name="Attachment Type")
    portrait_landscape = models.CharField(max_length=50, choices=[("Portrait", "Portrait"), ("Landscape", "Landscape")], verbose_name="Portrait / Landscape")
    story_num = models.FloatField(default=-1., verbose_name="# of Stories")
    season = models.CharField(max_length=200, verbose_name="Install Season")
    total_direct_time_hourly_employees = models.FloatField(default=-1., verbose_name="Total Direct Time for Project for Hourly Employees (Including Drive Time)")
    total_days_on_site = models.IntegerField(verbose_name="Total # of Days on Site")
    total_employees_on_site = models.IntegerField(verbose_name="Total # of Hourly Employees on Site")
    est_salary_empl = models.FloatField(default=-1., verbose_name="Estimated # of Salaried Employees on Site")
    est_salary_hr = models.FloatField(default=-1., verbose_name="Estimated Salary Hours") # in seconds
    est_direct_time = models.FloatField(verbose_name="Estimated Total Direct Time") # also seconds
    est_total_num_people_on_site = models.IntegerField(verbose_name="Estimated Total # of People on Site")
    notes = models.CharField(max_length=3000, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    @property
    def drive_time_minutes(self):
        return round(self.drive_time * 60)


    # Methods
    def __str__(self):
        field_values = []
        for field in self._meta.fields:
            field_name = field.name
            value = getattr(self, field_name)
            field_values.append(f"{field.verbose_name}: {value}")
        return " | ".join(field_values)"""
