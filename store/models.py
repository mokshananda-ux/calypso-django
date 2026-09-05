from django.db import models
from django.urls import reverse
from category.models import Category
from accounts.models import Account


# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='photos/products', blank=True)
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug, self.id])

    def __str__(self):
        return self.name


class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_user_product_review'
            )
        ]

    def __str__(self):
        return self.subject


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, null=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', blank=True, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'image'],
                name='unique_product_image'
            )
        ]

    def __str__(self):
        return self.product.name

