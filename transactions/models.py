from django.db import models

from shop.models import Customer


class Credit(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.FloatField()
    paid_amount = models.FloatField(default=0)
    due_date = models.DateField()
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def remaining_amount(self):
        return max(self.amount - self.paid_amount, 0)

    @property
    def is_cleared(self):
        return self.remaining_amount <= 0

    def __str__(self):
        return f"{self.customer.name} - {self.amount}"
