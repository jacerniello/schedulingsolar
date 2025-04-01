from django.db import models



class Data(models.Model):
    # Fields
    drive_time = models.FloatField(default=-1., name="drive_time")
    tilt = models.FloatField(default=-1., name="tilt")
    azimuth = models.FloatField(default=-1., name="azimuth")
    panel_qty = models.IntegerField(default=1, name="panel_qty")
    sys_rating = models.FloatField(default=-1., name="sys_rating")
    inv_manu = models.CharField(max_length=1000, name="inv_manu")
    array_type = models.CharField(max_length=1000, name="array_type")
    sqrl_screen = models.BooleanField(default=None, null=True, name="sqrl_screen")
    cons_monito = models.BooleanField(default=None, null=True, name="cons_monito")
    truss_rafter = models.CharField(max_length=10, name="truss_rafter")
    reinforcements = models.BooleanField(default=None, null=True, name="reinforcements")
    elec_inspec = models.BooleanField(default=None, null=True, name="elec_inspec")
    intercon_type = models.CharField(max_length=1000, name="intercon_type")
    module_len = models.FloatField(default=-1., name="module_len")
    module_width = models.FloatField(default=-1., name="module_width")
    module_weight = models.FloatField(default=-1., name="module_weight")
    array_num = models.FloatField(default=-1., name="array_num")
    circuit_num = models.FloatField(default=-1., name="circuit_num")
    reinforcement_num = models.FloatField(default=-1., name="reinforcement_num")
    roof_type = models.CharField(max_length=200, name="roof_type")
    attach_type = models.CharField(max_length=200, name="attach_type")
    story_num = models.FloatField(default=-1., name="story_num")
    season = models.CharField(max_length=200, name="season")
    est_salary_empl = models.FloatField(default=-1., name="est_salary_empl")
    est_salary_hr = models.FloatField(default=-1., name="est_salary_hr")
    est_direct_time = models.CharField(max_length=300, name="est_direct_time")
    created_at = models.DateTimeField(auto_now_add=True, name="created_at")

    # Methods
    def __str__(self):
        return f"Data(created_at={self.created_at})"