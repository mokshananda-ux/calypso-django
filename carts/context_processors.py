from .models import Cart, CartItem
from .views import _cart_id


def counter(request):
    if 'admin' in request.path:
        return {}

    cart = Cart.objects.filter(cart_id=_cart_id(request)).first()

    if cart:
        cart_count = CartItem.objects.filter(cart=cart).count()
    else:
        cart_count = 0

    return dict(cart_count=cart_count)