from django.contrib import admin
from django.urls import path
from . import views

appname = "sentiment_display"

urlpatterns = [
    path('', views.sentiment_displayer, name="sentiment_displayer"),
]