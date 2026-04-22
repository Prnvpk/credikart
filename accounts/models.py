from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('shopkeeper', 'Shopkeeper'),
        ('customer', 'Customer'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)