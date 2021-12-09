from django.contrib import admin
from django.urls import path
from . import views

appname = "displayer"
urlpatterns = [
    path('', views.home, name="display"),
    path('twitter/', views.twitter, name="twitter"),
]