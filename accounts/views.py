from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import CustomUser


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user_type = request.POST.get('user_type', 'customer')
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()

        if not username or not password or not email or not phone:
            messages.error(request, 'Username, email, phone number, and password are required.')

        elif user_type not in dict(CustomUser.USER_TYPE_CHOICES):
            messages.error(request, 'Please choose a valid account role.')

        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken.')

        elif CustomUser.objects.filter(email__iexact=email).exists():
            messages.error(request, 'That email is already registered.')

        elif CustomUser.objects.filter(phone=phone).exists():
            messages.error(request, 'That phone number is already registered.')
        else:
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                email=email,
                phone=phone,
                user_type=user_type,
            )
            if user_type == 'customer':
                from shop.models import Customer

                Customer.objects.filter(
                    linked_user__isnull=True,
                    email__iexact=email,
                    phone=phone,
                ).update(linked_user=user)
            messages.success(request, 'Account created successfully. Please sign in.')
            return redirect('login')

    return render(request, 'accounts/register.html')


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def user_logout(request):
    
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required(login_url='login')

def dashboard(request):

    role_labels = dict(CustomUser.USER_TYPE_CHOICES)
    user_role = role_labels.get(request.user.user_type, 'User')
    linked_customer_count = 0
    match_status = None
    customer_credit_count = 0
    customer_total_credit = 0
    customer_paid_credit = 0
    customer_remaining_credit = 0
    cleared_credit_count = 0
    recent_customer_credits = []
    cart_item_count = 0
    featured_products = []
    featured_product_count = 0

    if request.user.user_type == 'customer':
        from shop.models import Customer, Product
        from shop.views import CART_SESSION_KEY
        from transactions.models import Credit

        if request.user.email and request.user.phone:
            Customer.objects.filter(
                linked_user__isnull=True,
                email__iexact=request.user.email,
                phone=request.user.phone,
            ).update(linked_user=request.user)

        linked_customer_count = Customer.objects.filter(linked_user=request.user).count()

        if linked_customer_count:
            match_status = 'Matched with shopkeeper records using your email and phone number.'
            customer_credits = Credit.objects.filter(customer__linked_user=request.user).select_related('customer').order_by('-created_at')
            customer_credit_count = customer_credits.count()
            customer_total_credit = sum(credit.amount for credit in customer_credits)
            customer_paid_credit = sum(credit.paid_amount for credit in customer_credits)
            customer_remaining_credit = sum(credit.remaining_amount for credit in customer_credits)
            cleared_credit_count = sum(1 for credit in customer_credits if credit.is_cleared)
            recent_customer_credits = customer_credits[:3]
        else:
            match_status = 'No shopkeeper record matches your email and phone number yet.'

        cart_item_count = sum(
            int(quantity)
            for quantity in request.session.get(CART_SESSION_KEY, {}).values()
            if str(quantity).isdigit()
        )

        featured_products = list(
            Product.objects.filter(stock_quantity__gt=0)
            .select_related('shopkeeper')
            .order_by('-created_at')[:8]
        )
        featured_product_count = len(featured_products)

    context = {
        'user_role': user_role,
        'user_type': request.user.user_type,
        'match_status': match_status,
        'linked_customer_count': linked_customer_count,
        'customer_credit_count': customer_credit_count,
        'customer_total_credit': customer_total_credit,
        'customer_paid_credit': customer_paid_credit,
        'customer_remaining_credit': customer_remaining_credit,
        'cleared_credit_count': cleared_credit_count,
        'recent_customer_credits': recent_customer_credits,
        'cart_item_count': cart_item_count,
        'featured_products': featured_products,
        'featured_product_count': featured_product_count,
    }
    return render(request, 'accounts/dashboard.html', context)
