from django.db import models
from accounts.models import Account
from store.models import Product

# Create your models here.

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_product_per_cart",
                condition=models.Q(cart__isnull=False),
                violation_error_message="Este producto ya está en el carrito de sesión."
            )
        ]
        # Nota: La unicidad para user+product se maneja a nivel de aplicación
        # para evitar conflictos con la migración de cart a user durante el login

    def __str__(self):
        return str(self.product)