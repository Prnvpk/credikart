from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction

from shop.models import Customer, Product
from shop.views import CART_SESSION_KEY

from .models import Credit


def _build_cart_items(request):
    raw_cart = request.session.get(CART_SESSION_KEY, {})
    product_ids = [int(product_id) for product_id in raw_cart.keys()]
    products = Product.objects.filter(id__in=product_ids).select_related('shopkeeper')
    product_lookup = {product.id: product for product in products}
    items = []
    total_amount = Decimal('0.00')
    total_quantity = 0

    for product_id, quantity in raw_cart.items():
        try:
            product_key = int(product_id)
            quantity_value = int(quantity)
        except (TypeError, ValueError):
            continue

        if quantity_value <= 0:
            continue

        product = product_lookup.get(product_key)
        if product is None:
            continue

        subtotal = product.price * quantity_value
        items.append(
            {
                'product': product,
                'quantity': quantity_value,
                'subtotal': subtotal,
            }
        )
        total_amount += subtotal
        total_quantity += quantity_value

    return items, total_amount, total_quantity


@login_required
def add_credit(request):
    if request.user.user_type != 'shopkeeper':
        messages.error(request, 'Only shopkeepers can create credit entries.')
        return redirect('dashboard')

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

    credits = credits.select_related('customer', 'customer__shopkeeper').order_by('-created_at')
    total_credit_amount = sum(credit.amount for credit in credits)
    total_paid_amount = sum(credit.paid_amount for credit in credits)
    total_balance_amount = sum(credit.remaining_amount for credit in credits)
    cleared_credit_count = sum(1 for credit in credits if credit.is_cleared)

    context = {
        'credits': credits,
        'is_shopkeeper': request.user.user_type == 'shopkeeper',
        'total_credit_amount': total_credit_amount,
        'total_paid_amount': total_paid_amount,
        'total_balance_amount': total_balance_amount,
        'cleared_credit_count': cleared_credit_count,
    }
    return render(request, 'transactions/credit_list.html', context)


@login_required
def payment_page(request):
    if request.user.user_type != 'customer':
        messages.error(request, 'Only customers can continue to payment.')
        return redirect('dashboard')

    cart_items, total_amount, total_quantity = _build_cart_items(request)
    if not cart_items:
        messages.error(request, 'Your cart is empty. Add products before continuing to payment.')
        return redirect('cart_view')

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'total_quantity': total_quantity,
    }
    return render(request, 'transactions/payment_page.html', context)


@login_required
def pay_later(request):
    if request.user.user_type != 'customer':
        messages.error(request, 'Only customers can use pay later.')
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('payment_page')

    cart_items, total_amount, total_quantity = _build_cart_items(request)
    if not cart_items:
        messages.error(request, 'Your cart is empty. Add products before using pay later.')
        return redirect('cart_view')

    missing_links = []
    credits_to_create = {}

    for item in cart_items:
        product = item['product']
        if item['quantity'] > product.stock_quantity:
            messages.error(
                request,
                f'Only {product.stock_quantity} units of "{product.name}" are available now. Please update your cart and try again.',
            )
            return redirect('cart_view')

        customer_record = Customer.objects.filter(
            shopkeeper=product.shopkeeper,
            linked_user=request.user,
        ).first()

        if customer_record is None:
            missing_links.append(product.shopkeeper.username)
            continue

        group = credits_to_create.setdefault(
            customer_record.id,
            {
                'customer': customer_record,
                'amount': Decimal('0.00'),
                'details': [],
            },
        )
        group['amount'] += item['subtotal']
        group['details'].append(f"{product.name} x {item['quantity']}")

    if missing_links:
        seller_names = ', '.join(sorted(set(missing_links)))
        messages.error(
            request,
            f'You can only use pay later with linked shopkeepers. Missing customer link for: {seller_names}.',
        )
        return redirect('cart_view')

    with transaction.atomic():
        for item in cart_items:
            product = Product.objects.select_for_update().get(id=item['product'].id)
            if item['quantity'] > product.stock_quantity:
                messages.error(
                    request,
                    f'"{product.name}" stock changed while processing. Please review your cart again.',
                )
                return redirect('cart_view')
            product.stock_quantity -= item['quantity']
            product.save(update_fields=['stock_quantity'])

        for group in credits_to_create.values():
            Credit.objects.create(
                customer=group['customer'],
                amount=float(group['amount']),
                paid_amount=0,
                due_date=date.today(),
                details=', '.join(group['details']),
            )

    request.session[CART_SESSION_KEY] = {}
    request.session.modified = True
    messages.success(
        request,
        f'Pay later saved successfully. Rs. {total_amount} was moved to your credit records for {total_quantity} item(s).',
    )
    return redirect('credit_list')
