"""
URL configuration for schedulingsolar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
import app.views as views


urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.home, name="home"),
    path("input/", views.update, name="input"),
    path("delete/", views.delete_data, name="delete_data"),

    path("save/", views.save_data),
    path("search/", views.search_data, name="search"),
    path("view/<int:project_id>", views.view_data),
    path("edit/", views.edit_data),


    path("custom-admin/", views.custom_admin, name="custom_admin"),

    path("save-input-field/", views.save_input_field, name="save_input_field"),

    path("edit-model-type/", views.edit_model_type, name="edit_model_type"),
    path("analyze-file/", views.analyze_file, name="analyze_file"),

    path("train/", views.train, name="train"),
    path("time-estimate/<int:project_id>", views.time_estimate, name="time_estimate"),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("__reload__/", include("django_browser_reload.urls"))
]
