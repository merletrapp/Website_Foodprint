from django.db import models

# Create your models here.
class Food(models.Model):
    BASE_UNITS = [
        ("kg", "Kilogramm"),
        ("l", "Liter"),
    ]
    name = models.CharField(max_length=255)
    co2_score= models.DecimalField(max_digits=4, decimal_places=1)
    base_unit = models.CharField(max_length=2, choices=BASE_UNITS, default="kg")