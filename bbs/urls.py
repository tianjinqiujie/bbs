"""bbs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.urls import path,re_path
from blog import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login),
    path('code/', views.code),
    path('reg/', views.register),
    path('index/',views.index),
    path('logout/',views.logout),
    path('digg/',views.digg),
    path('comment/', views.comment),
    path('backend/', views.backend),
    path('backend/add_article/', views.add_article),
    path('upload/', views.upload),
    path('backend/delete_article/',views.delete_article),
    re_path('backend/edit_article/(?P<edit_id>\d+)$', views.edit_article),
    path('',views.index),
    re_path('(?P<username>\w+)/articles/(?P<article_id>\d+)$', views.article_detail),
    re_path('(?P<username>\w+)/(?P<condition>category|tag|achrive)/(?P<params>.*)',views.homesite),
    re_path('(?P<username>\w+)/$',views.homesite)
]
