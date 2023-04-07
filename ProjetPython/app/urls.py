# -*- coding: utf-8 -*-
"""
Created on Fri May 20 16:07:26 2022

@author: nutel
"""
from django.urls import path,include
from . import views
from django.http import HttpResponse


urlpatterns = [
    path('', views.fonction1,name='mystere'), #si on met rien on cherche la fonction index dans views.py et on l'execute
    path('test1',views.model1,name='model1')
]

