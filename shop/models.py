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
