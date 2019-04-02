"""greece_logic URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.shortcuts import render
from django.urls import path

from ndvi.views import ImageView, StatsView, ListLayersView, ColorView


def leaflet_map(request):
    """
    Show the slippy map as a view
    :param request:
    :return:
    """
    return render(request, 'leaflet_map.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('layers/', ListLayersView.as_view()),
    path('image/', ImageView.as_view()),
    path('stats/', StatsView.as_view()),
    path('', leaflet_map),
    path('color/', ColorView.as_view())
]
