from datetime import date

from .models import Credit
from shop.models import Customer
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render


@login_required
def add_credit(request):
    customers = Customer.objects.filter(shopkeeper=request.user)
    context = {
        'customers': customers,
        'today': date.today().isoformat(),
    }

    if request.method == 'POST':
        customer_id = request.POST.get('customer', '')
        amount = request.POST.get('amount', '')
        due_date_value = request.POST.get('due_date', '')
        context['form_data'] = {
            'customer': customer_id,
            'amount': amount,
            'due_date': due_date_value,
        }

        try:
            due_date = date.fromisoformat(due_date_value)
        except ValueError:
            context['error_message'] = 'Please enter a valid due date.'
            return render(request, 'transactions/add_credit.html', context)

        if due_date > date.today():
            context['error_message'] = 'Future due dates are not allowed.'
            return render(request, 'transactions/add_credit.html', context)

        customer = get_object_or_404(Customer, id=customer_id, shopkeeper=request.user)

        Credit.objects.create(customer=customer, amount=amount, due_date=due_date)

        return redirect('credit_list')

    return render(request, 'transactions/add_credit.html', context)


@login_required
def credit_list(request):
    if request.user.user_type == 'customer':
        credits = Credit.objects.filter(customer__linked_user=request.user)
    else:
        credits = Credit.objects.filter(customer__shopkeeper=request.user)

    context = {
        'credits': credits,
        'is_shopkeeper': request.user.user_type == 'shopkeeper',
    }
    return render(request, 'transactions/credit_list.html', context)
