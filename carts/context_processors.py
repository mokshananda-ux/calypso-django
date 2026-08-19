from .models import Cart, CartItem
from .views import _cart_id


def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}

    try:
        if request.user.is_authenticated:
            # Para usuarios autenticados, contar items de su carrito
            cart_count = CartItem.objects.filter(user=request.user, is_active=True).count()
        else:
            # Para usuarios invitados, contar items del carrito de sesión
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_count = CartItem.objects.filter(cart=cart, is_active=True).count()
    except Cart.DoesNotExist:
        cart_count = 0

    return dict(cart_count=cart_count)