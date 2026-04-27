from django.urls import path
from . import views

urlpatterns = [
    path('add-customer/', views.add_customer, name='add_customer'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/<int:customer_id>/manual-match/', views.manual_match_customer, name='manual_match_customer'),
]
