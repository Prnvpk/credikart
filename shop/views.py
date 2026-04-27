from accounts.models import CustomUser
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Customer


@login_required
def add_customer(request):
    if request.user.user_type != 'shopkeeper':
        messages.error(request, 'Only shopkeepers can add customers.')
        return redirect('dashboard')

    context = {}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        context['form_data'] = {
            'name': name,
            'email': email,
            'phone': phone,
        }

        if not name or not email or not phone:
            context['error_message'] = 'Name, email, and phone number are required.'
            return render(request, 'shop/add_customer.html', context)

        if Customer.objects.filter(shopkeeper=request.user, email__iexact=email).exists():
            context['error_message'] = 'This email is already added to your customer list.'
            return render(request, 'shop/add_customer.html', context)

        linked_user = CustomUser.objects.filter(
            email__iexact=email,
            phone=phone,
            user_type='customer',
        ).first()

        Customer.objects.create(
            shopkeeper=request.user,
            linked_user=linked_user,
            name=name,
            email=email,
            phone=phone,
        )

        return redirect('customer_list')

    return render(request, 'shop/add_customer.html', context)


@login_required
def customer_list(request):
    if request.user.user_type != 'shopkeeper':
        messages.error(request, 'Only shopkeepers can view customer records.')
        return redirect('dashboard')

    customers = Customer.objects.filter(shopkeeper=request.user).select_related('linked_user')
    return render(request, 'shop/customer_list.html', {'customers': customers})


@login_required
def manual_match_customer(request, customer_id):
    if request.user.user_type != 'shopkeeper':
        messages.error(request, 'Only shopkeepers can manually match customers.')
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('customer_list')

    customer = get_object_or_404(Customer, id=customer_id, shopkeeper=request.user)
    username = request.POST.get('customer_username', '').strip()

    if not username:
        messages.error(request, f'Enter a customer username to link with {customer.name}.')
        return redirect('customer_list')

    linked_user = CustomUser.objects.filter(username=username, user_type='customer').first()
    if linked_user is None:
        messages.error(request, f'No customer account found with username "{username}".')
        return redirect('customer_list')

    already_linked = Customer.objects.filter(
        shopkeeper=request.user,
        linked_user=linked_user,
    ).exclude(id=customer.id).exists()
    if already_linked:
        messages.error(request, f'The customer account "{username}" is already linked to another record in your list.')
        return redirect('customer_list')

    customer.linked_user = linked_user
    customer.save(update_fields=['linked_user'])
    messages.success(request, f'{customer.name} is now linked to customer login "{username}".')
    return redirect('customer_list')
