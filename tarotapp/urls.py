from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('predict/', views.predict, name='predict'),
    path('draw/', views.draw_cards, name='draw_cards'),
]
