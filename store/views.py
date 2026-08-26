from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category
from .models import Product, ReviewRating
from .forms import ReviewForm
from django.db.models import Q
from django.contrib import messages
from orders.models import OrderProduct


# Create your views here.

def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        paginator = Paginator(products, 2)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 4)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()


    
    context = {
        'products': paged_products,
        'product_count': product_count,
        }

    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)

        # Verificar si el producto está en el carrito según el estado de autenticación
        if request.user.is_authenticated:
            in_cart = CartItem.objects.filter(user=request.user, product=single_product, is_active=True).exists()
        else:
            in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product, is_active=True).exists()

    except Exception as e:
        raise e

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
    }

    return render(request, 'store/product_detail.html', context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_at').filter(
                Q(description__icontains=keyword) | Q(name__icontains=keyword)
            )
            product_count = products.count()

        context = {
            'products': products,
            'product_count': product_count,
        }   
        
    return render(request, 'store/store.html', context)

def submit_review(request, product_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión para escribir una reseña.')
        return redirect('login')

    # Verificar si el usuario ha comprado este producto
    try:
        order_product = OrderProduct.objects.get(
            user=request.user,
            product_id=product_id,
            order__is_ordered=True,
            payment__status='COMPLETED',
        )
    except OrderProduct.DoesNotExist:
        messages.error(request, 'Solo puedes reseñar productos que has comprado.')
        return redirect('my_reviews')

    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user_id=request.user.id, product_id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Gracias! Tu reseña ha sido actualizada.')
            return redirect('my_reviews')
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Gracias! Tu reseña ha sido enviada.')
                return redirect('my_reviews')
