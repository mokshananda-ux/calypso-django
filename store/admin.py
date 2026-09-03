from django.contrib import admin
from .models import Product, ReviewRating, ProductGallery
from easy_thumbnails.files import get_thumbnailer


class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

    def thumbnail_image(self, obj):
        if obj.image:
            thumbnailer = get_thumbnailer(obj.image)
            thumbnail = thumbnailer.get_thumbnail({'size': (100, 100), 'crop': True})
            return f'<img src="{thumbnail.url}" width="100" height="100" />'
        return 'No image'
    thumbnail_image.short_description = 'Thumbnail'
    thumbnail_image.allow_tags = True

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_available', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_available',)
    list_filter = ('is_available', 'category')
    search_fields = ('name', 'description')
    inlines = [ProductGalleryInline]
    readonly_fields = ('thumbnail_preview',)

    def thumbnail_preview(self, obj):
        if obj.image:
            thumbnailer = get_thumbnailer(obj.image)
            thumbnail = thumbnailer.get_thumbnail({'size': (300, 300), 'crop': True})
            return f'<img src="{thumbnail.url}" width="300" height="300" />'
        return 'No image'
    thumbnail_preview.short_description = 'Preview'
    thumbnail_preview.allow_tags = True

# Register your models here.

admin.site.register(Product, ProductAdmin)

admin.site.register(ReviewRating)

admin.site.register(ProductGallery)
