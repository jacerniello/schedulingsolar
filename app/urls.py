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
from . import views
from . import update_server

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.home, name="home"),
    path("input/", views.update, name="input"),
    path("save/", views.save_data),
    path("view/", views.view_data),
    path("edit/", views.edit_data),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("update_server/", update_server.GithubUpdate.as_view()),
    path("__reload__/", include("django_browser_reload.urls")),
]
