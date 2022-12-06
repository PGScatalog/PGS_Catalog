"""pgs_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.conf import settings
from django.urls import include, path, re_path
from search import views as search_views

urlpatterns = [
	path('', include('catalog.urls')),
    path('', include('rest_api.urls')),
    re_path(r'^search/', search_views.search, name="PGS Catalog Search"),
    re_path(r'^autocomplete/', search_views.autocomplete, name="PGS Catalog Autocomplete")
]
if settings.PGS_ON_CURATION_SITE == 'True':
    from django.contrib import admin
    urlpatterns.append(path('admin/', admin.site.urls))
