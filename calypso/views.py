from  django.shortcuts import render

from store.models import Product, ReviewRating

def home(request):
    products = Product.objects.all().filter(is_available=True)
    recent_reviews = ReviewRating.objects.filter(status=True).order_by('-created_at')[:5]

    context = {
        'products': products,
        'recent_reviews': recent_reviews,
    }

    return render(request, 'home.html', context)