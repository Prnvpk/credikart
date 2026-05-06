from django.urls import path
from . import views

urlpatterns = [
    path('add-credit/', views.add_credit, name='add_credit'),
    path('credits/', views.credit_list, name='credit_list'),
    path('payment/', views.payment_page, name='payment_page'),
    path('pay-later/', views.pay_later, name='pay_later'),
]
