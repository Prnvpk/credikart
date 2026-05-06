from django.urls import path
from . import views

urlpatterns = [
    path('add-customer/', views.add_customer, name='add_customer'),
    path('customers/', views.customer_list, name='customer_list'),
    path('add-product/', views.add_product, name='add_product'),
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:product_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('products/', views.product_list, name='product_list'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/<int:product_id>/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('customers/<int:customer_id>/manual-match/', views.manual_match_customer, name='manual_match_customer'),
]
