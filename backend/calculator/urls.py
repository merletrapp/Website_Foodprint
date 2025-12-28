from django.urls import path
from .views import foods, food, foods_calculate

urlpatterns = [
    path('foods/', foods,  name='foods'),
    path("foods/<int:id>/", food, name="food"),
    path("foods/calculate/", foods_calculate, name="foods-calculate"), 
]