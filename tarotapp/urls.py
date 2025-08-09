from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('predict/', views.predict, name='predict'),
    path('draw/', views.draw_cards, name='draw_cards'),
    path('video_prediction/', views.video_prediction, name='video_prediction'),
]
