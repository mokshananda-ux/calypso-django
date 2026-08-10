from django.contrib import admin
from .models import Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_available', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_available',)
    list_filter = ('is_available', 'category')
    search_fields = ('name', 'description')

# Register your models here.

admin.site.register(Product, ProductAdmin)
