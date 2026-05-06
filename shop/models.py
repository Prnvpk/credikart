from accounts.models import CustomUser
from django.db import models


class Customer(models.Model):
    shopkeeper = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    linked_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_records',
        limit_choices_to={'user_type': 'customer'},
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['shopkeeper', 'email'],
                name='unique_customer_email_per_shopkeeper',
            )
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    shopkeeper = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='products',
        limit_choices_to={'user_type': 'shopkeeper'},
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    image = models.FileField(upload_to='products/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['shopkeeper', 'name'],
                name='unique_product_name_per_shopkeeper',
            )
        ]

    def __str__(self):
        return self.name
