from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category
from .models import Product, ReviewRating, ProductGallery
from .forms import ReviewForm
from django.db.models import Q
from django.contrib import messages
from orders.models import OrderProduct
from django.views.decorators.http import require_POST


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


def product_detail(request, category_slug, product_slug, product_id):
    try:
        single_product = Product.objects.get(id=product_id, category__slug=category_slug, slug=product_slug)

        # Verificar si el producto está en el carrito según el estado de autenticación
        if request.user.is_authenticated:
            in_cart = CartItem.objects.filter(user=request.user, product=single_product, is_active=True).exists()
        else:
            in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product, is_active=True).exists()

    except Exception as e:
        raise e

    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'product_gallery': product_gallery,
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

@require_POST
def submit_review(request, product_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión para escribir una reseña.')
        return redirect('login')

    purchased = OrderProduct.objects.filter(
        user=request.user,
        product_id=product_id,
        order__is_ordered=True,
        payment__status='COMPLETED',
    ).exists()

    if not purchased:
        messages.error(
            request,
            'Solo puedes reseñar productos que has comprado.'
        )
        return redirect('my_reviews')

    existing_review = ReviewRating.objects.filter(
        user=request.user,
        product_id=product_id,
    ).first()

    form = ReviewForm(request.POST, instance=existing_review)

    if not form.is_valid():
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
        return redirect('my_reviews')

    review = form.save(commit=False)
    review.user = request.user
    review.product_id = product_id
    review.ip = request.META.get('REMOTE_ADDR', '')
    review.status = True
    review.save()

    if existing_review:
        messages.success(request, 'Gracias. Tu reseña ha sido actualizada.')
    else:
        messages.success(request, 'Gracias por tu reseña.')

    return redirect('my_reviews')

@login_required(login_url='login')
def edit_review(request, product_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión para editar una reseña.')
        return redirect('login')

    purchased = OrderProduct.objects.filter(
        user=request.user,
        product_id=product_id,
        order__is_ordered=True,
        payment__status='COMPLETED',
    ).exists()

    if not purchased:
        messages.error(
            request,
            'Solo puedes editar reseñas de productos que has comprado.'
        )
        return redirect('my_reviews')

    review = get_object_or_404(
        ReviewRating,
        user=request.user,
        product_id=product_id
    )

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu reseña ha sido actualizada.')
            return redirect('my_reviews')
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    else:
        form = ReviewForm(instance=review)

    context = {
        'form': form,
        'review': review,
        'product': review.product,
    }
    return render(request, 'store/edit_review.html', context)

@login_required(login_url='login')
def create_review(request, product_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión para escribir una reseña.')
        return redirect('login')

    purchased = OrderProduct.objects.filter(
        user=request.user,
        product_id=product_id,
        order__is_ordered=True,
        payment__status='COMPLETED',
    ).exists()

    if not purchased:
        messages.error(
            request,
            'Solo puedes reseñar productos que has comprado.'
        )
        return redirect('my_reviews')

    existing_review = ReviewRating.objects.filter(
        user=request.user,
        product_id=product_id,
    ).first()

    if existing_review:
        messages.info(request, 'Ya has escrito una reseña para este producto. Puedes editarla.')
        return redirect('edit_review', product_id=product_id)

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.ip = request.META.get('REMOTE_ADDR', '')
            review.status = True
            review.save()
            messages.success(request, 'Gracias por tu reseña.')
            return redirect('my_reviews')
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'store/create_review.html', context)





recent_reviews = ReviewRating.objects.filter(
    status=True
).select_related('user', 'product').order_by('-created_at')[:10]
