from django.shortcuts import redirect, render, get_object_or_404
from .models import Cart, CartItem
from store.models import Product
from django.core.exceptions import ObjectDoesNotExist


def _cart_id(request):
    cart = request.session.session_key

    if not cart:
        cart = request.session.create()

    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))

    CartItem.objects.get_or_create(
        product=product,
        cart=cart
    )

    return redirect('cart')


def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)

    cart_item.delete()

    return redirect('cart')



def cart(request):
    total = 0
    cart_items = []

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))

        cart_items = CartItem.objects.filter(
            cart=cart,
            is_active=True
        )

        for cart_item in cart_items:
            total += cart_item.product.price
        # Sum totals for all cart items; calculate tax and grand_total afterwards

    except Cart.ObjectDoesNotExist:
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
