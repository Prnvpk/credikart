from decimal import Decimal, InvalidOperation

from accounts.models import CustomUser
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .models import Customer, Product


CART_SESSION_KEY = 'customer_cart'


def _get_cart(request):
    return request.session.get(CART_SESSION_KEY, {})


def _save_cart(request, cart):
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def _build_cart_items(request):
    raw_cart = _get_cart(request)
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
def add_product(request):
    if request.user.user_type != 'shopkeeper':
        messages.error(request, 'Only shopkeepers can add products.')
        return redirect('dashboard')

    context = {}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '').strip()
        stock_quantity = request.POST.get('stock_quantity', '').strip()
        image = request.FILES.get('image')
        context['form_data'] = {
            'name': name,
            'description': description,
            'price': price,
            'stock_quantity': stock_quantity,
        }

        if not name or not price or stock_quantity == '':
            context['error_message'] = 'Name, price, and stock quantity are required.'
            return render(request, 'shop/add_product.html', context)

        if Product.objects.filter(shopkeeper=request.user, name__iexact=name).exists():
            context['error_message'] = 'A product with this name already exists in your catalog.'
            return render(request, 'shop/add_product.html', context)

        try:
            price_value = Decimal(price)
        except InvalidOperation:
            context['error_message'] = 'Enter a valid price.'
            return render(request, 'shop/add_product.html', context)

        if price_value < 0:
            context['error_message'] = 'Price cannot be negative.'
            return render(request, 'shop/add_product.html', context)

        try:
            stock_quantity_value = int(stock_quantity)
        except ValueError:
            context['error_message'] = 'Enter a valid stock quantity.'
            return render(request, 'shop/add_product.html', context)

        if stock_quantity_value < 0:
            context['error_message'] = 'Stock quantity cannot be negative.'
            return render(request, 'shop/add_product.html', context)

        Product.objects.create(
            shopkeeper=request.user,
            name=name,
            description=description,
            image=image,
            price=price_value,
            stock_quantity=stock_quantity_value,
        )
        messages.success(request, f'"{name}" was added to your product catalog.')
        return redirect('product_list')

    return render(request, 'shop/add_product.html', context)


@login_required
def edit_product(request, product_id):
    if request.user.user_type != 'shopkeeper':
        messages.error(request, 'Only shopkeepers can edit products.')
        return redirect('dashboard')

    product = get_object_or_404(Product, id=product_id, shopkeeper=request.user)
    context = {
        'product': product,
        'form_data': {
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock_quantity': product.stock_quantity,
        },
        'is_edit_mode': True,
    }

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '').strip()
        stock_quantity = request.POST.get('stock_quantity', '').strip()
        image = request.FILES.get('image')
        context['form_data'] = {
            'name': name,
            'description': description,
            'price': price,
            'stock_quantity': stock_quantity,
        }

        if not name or not price or stock_quantity == '':
            context['error_message'] = 'Name, price, and stock quantity are required.'
            return render(request, 'shop/add_product.html', context)

        if Product.objects.filter(shopkeeper=request.user, name__iexact=name).exclude(id=product.id).exists():
            context['error_message'] = 'A product with this name already exists in your catalog.'
            return render(request, 'shop/add_product.html', context)

        try:
            price_value = Decimal(price)
        except InvalidOperation:
            context['error_message'] = 'Enter a valid price.'
            return render(request, 'shop/add_product.html', context)

        if price_value < 0:
            context['error_message'] = 'Price cannot be negative.'
            return render(request, 'shop/add_product.html', context)

        try:
            stock_quantity_value = int(stock_quantity)
        except ValueError:
            context['error_message'] = 'Enter a valid stock quantity.'
            return render(request, 'shop/add_product.html', context)

        if stock_quantity_value < 0:
            context['error_message'] = 'Stock quantity cannot be negative.'
            return render(request, 'shop/add_product.html', context)

        product.name = name
        product.description = description
        product.price = price_value
        product.stock_quantity = stock_quantity_value
        if image:
            product.image = image
        product.save()

        messages.success(request, f'"{product.name}" was updated successfully.')
        return redirect('product_list')

    return render(request, 'shop/add_product.html', context)


@login_required
def product_list(request):
    products_per_page = 12

    if request.user.user_type == 'shopkeeper':
        products = Product.objects.filter(shopkeeper=request.user).select_related('shopkeeper')
        shopkeepers = []
        selected_shopkeeper_id = ''
        page_title = 'Your Products'
        subtitle = 'Manage the products available in your shop before they are used in customer purchases and credit records.'
        empty_state = 'No products added yet.'
        can_add_products = True
    elif request.user.user_type == 'customer':
        shopkeepers = CustomUser.objects.filter(
            user_type='shopkeeper',
            products__isnull=False,
        ).distinct().order_by('username')
        selected_shopkeeper_id = request.GET.get('shopkeeper', '').strip()
        products = Product.objects.filter(shopkeeper__in=shopkeepers).select_related('shopkeeper').distinct()
        if selected_shopkeeper_id and shopkeepers.filter(id=selected_shopkeeper_id).exists():
            products = products.filter(shopkeeper_id=selected_shopkeeper_id)
        else:
            selected_shopkeeper_id = ''
        page_title = 'Available Products'
        subtitle = 'Browse products, add them to your cart, and continue to the payment page whenever you are ready.'
        empty_state = (
            'No products are available for the selected shopkeeper yet.'
            if selected_shopkeeper_id
            else 'No products are available from any shopkeeper yet.'
        )
        can_add_products = False
    else:
        messages.error(request, 'You do not have access to products.')
        return redirect('dashboard')

    total_products = products.count()
    paginator = Paginator(products, products_per_page)
    page_obj = paginator.get_page(request.GET.get('page'))
    products = page_obj.object_list
    _, _, cart_item_count = _build_cart_items(request) if request.user.user_type == 'customer' else ([], Decimal('0.00'), 0)

    context = {
        'products': products,
        'page_obj': page_obj,
        'products_per_page': products_per_page,
        'total_products': total_products,
        'page_title': page_title,
        'subtitle': subtitle,
        'empty_state': empty_state,
        'can_add_products': can_add_products,
        'is_customer': request.user.user_type == 'customer',
        'shopkeepers': shopkeepers,
        'selected_shopkeeper_id': selected_shopkeeper_id,
        'cart_item_count': cart_item_count,
    }
    return render(request, 'shop/product_list.html', context)


@login_required
def add_to_cart(request, product_id):
    if request.user.user_type != 'customer':
        messages.error(request, 'Only customers can add items to the cart.')
        return redirect('product_list')

    if request.method != 'POST':
        return redirect('product_list')

    product = get_object_or_404(Product, id=product_id)
    if product.stock_quantity <= 0:
        messages.error(request, f'"{product.name}" is currently out of stock.')
        return redirect('product_list')

    cart = _get_cart(request)
    current_quantity = int(cart.get(str(product.id), 0))

    if current_quantity >= product.stock_quantity:
        messages.error(request, f'Only {product.stock_quantity} units of "{product.name}" are available right now.')
        return redirect('product_list')

    cart[str(product.id)] = current_quantity + 1
    _save_cart(request, cart)
    messages.success(request, f'"{product.name}" was added to your cart.')
    return redirect('product_list')


@login_required
def cart_view(request):
    if request.user.user_type != 'customer':
        messages.error(request, 'Only customers can access the cart.')
        return redirect('dashboard')

    cart_items, total_amount, total_quantity = _build_cart_items(request)
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'total_quantity': total_quantity,
    }
    return render(request, 'shop/cart.html', context)


@login_required
def remove_from_cart(request, product_id):
    if request.user.user_type != 'customer':
        messages.error(request, 'Only customers can update the cart.')
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('cart_view')

    cart = _get_cart(request)
    if str(product_id) in cart:
        cart.pop(str(product_id), None)
        _save_cart(request, cart)
        messages.success(request, 'Item removed from your cart.')

    return redirect('cart_view')


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
