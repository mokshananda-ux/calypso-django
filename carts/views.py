from django.shortcuts import redirect, render, get_object_or_404
from .models import Cart, CartItem
from store.models import Product
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required 


def _cart_id(request):
    cart = request.session.session_key

    if not cart:
        cart = request.session.create()

    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)

    if request.user.is_authenticated:
        # Para usuarios autenticados, verificar si ya tiene el producto
        existing_item = CartItem.objects.filter(
            user=request.user,
            product=product,
            is_active=True
        ).first()

        if existing_item:
            return redirect('cart')

        # Crear o usar un cart de sesión para mantener consistencia
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))

        cart_item = CartItem.objects.create(
            product=product,
            cart=cart,
            user=request.user,
            is_active=True
        )
    else:
        # Para usuarios invitados, usar el carrito de sesión
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))

        cart_item, _ = CartItem.objects.get_or_create(
            product=product,
            cart=cart,
            defaults={'is_active': True}
        )

    return redirect('cart')


def remove_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        # Para usuarios autenticados, eliminar de su carrito de usuario
        cart_item = CartItem.objects.get(product=product, user=request.user)
    else:
        # Para usuarios invitados, eliminar del carrito de sesión
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart)

    cart_item.delete()

    return redirect('cart')



def cart(request):
    total = 0
    cart_items = []

    try:
        if request.user.is_authenticated:
            # Para usuarios autenticados, usar su carrito de usuario
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            # Para usuarios invitados, usar el carrito de sesión
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(
                cart=cart,
                is_active=True
            )

        for cart_item in cart_items:
            total += cart_item.product.price

    except Cart.DoesNotExist:
        pass

    # Calculate tax and grand total even if cart does not exist or is empty
    tax = (2 * total) / 100
    grand_total = total + tax

    context = {
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
        'cart_items': cart_items,
    }

    return render(request, 'store/cart.html', context)



@login_required(login_url='login')
def checkout(request):
    total = 0
    cart_items = []

    try:
        # Para usuarios autenticados, usar su carrito de usuario
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)

        for cart_item in cart_items:
            total += cart_item.product.price

    except Exception:
        pass

    # Calculate tax and grand total even if cart does not exist or is empty
    tax = (2 * total) / 100
    grand_total = total + tax

    context = {
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
        'cart_items': cart_items,
    }
    return render(request, 'store/checkout.html', context)