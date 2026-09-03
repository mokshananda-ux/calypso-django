from django.contrib import auth, messages
from django.shortcuts import redirect, render, get_object_or_404
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.contrib.auth.decorators import login_required

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import _cart_id
from carts.models import Cart, CartItem
from orders.models import Order, OrderProduct
from store.models import ReviewRating


#verification email

import requests


def register(request):
    form = None
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            username = email.split('@')[0]  # Generate username from email
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            #user activation logic can be added here if needed
            current_site = get_current_site(request)
            mail_subject = 'Por favor, activa tu cuenta'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            return redirect('/accounts/login/?command=verification&email=' + email)
    else:
        form = RegistrationForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_items = CartItem.objects.filter(cart=cart)

                    for item in cart_items:
                        # Verificar si el usuario ya tiene este producto en su carrito
                        existing_user_item = CartItem.objects.filter(
                            user=user,
                            product=item.product,
                            is_active=True
                        ).first()

                        if existing_user_item:
                            # El usuario ya tiene este producto, eliminar el item de sesión
                            item.delete()
                        else:
                            # Asignar el item al usuario
                            item.user = user
                            item.save()

            except:
                pass

            auth.login(request, user)
            # User is authenticated, you can log them in
            messages.success(request, '!Has hecho login con éxito¡')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']  
                return redirect(nextPage)
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'Email inválido o contraseña incorrecta. Por favor, inténtalo de nuevo.')
            return redirect('login')  # Redirect back to login page on failure

    return render(request, 'accounts/login.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'Has cerrado sesión con éxito.')
    return redirect('home')  # Redirect to home page after logout

def activate(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True 
        user.save()
        messages.success(request, '¡Felicidades!, tu cuenta ha sido activada')
        return redirect('login')
    else:
        messages.error(request, 'Lo sentimos, vínculo de activación incorrecto')
        return redirect('register')


@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    # Get profile picture or create if doesn't exist
    try:
        userprofile = UserProfile.objects.get(user_id=request.user.id)
    except UserProfile.DoesNotExist:
        userprofile = UserProfile.objects.create(user=request.user)
    
    context = {
        'orders': orders,
        'orders_count': orders_count,
        'userprofile': userprofile
    }
    return render(request, 'accounts/dashboard.html', context)


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if Account.objects.filter(email__iexact=email).exists():
            user = Account.objects.get(email__iexact=email)
            current_site = get_current_site(request)
            mail_subject = 'Restablecer tu contraseña'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'Se ha enviado un correo electrónico para restablecer tu contraseña.')
            return redirect('login')
        else:
            messages.error(request, 'La cuenta con este correo electrónico no existe.')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Por favor restablece tu contraseña')
        return redirect('resetPassword')  # Redirect to login page after successful validation
    else:
        messages.error(request, 'El enlace ha caducado')
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Tu contraseña ha sido restablecida con éxito.')
            return redirect('login')  # Redirect to login page after successful password reset
        else:
            messages.error(request, 'Las contraseñas no coinciden. Por favor, inténtalo de nuevo.')
            return redirect('resetPassword')  # Redirect back to reset password page on failure

    return render(request, 'accounts/resetPassword.html')


@login_required(login_url='login')
def my_reviews(request):
    purchased_products = OrderProduct.objects.filter(
        user=request.user,
        order__is_ordered=True,
        payment__status='COMPLETED',
    ).select_related('product').order_by('-created_at')

    user_reviews = ReviewRating.objects.filter(
        user=request.user
    ).select_related('product').order_by('-created_at')

    reviews_by_product = {
        review.product_id: review
        for review in user_reviews
    }

    reviewed_products = set(reviews_by_product.keys())

    for item in purchased_products:
        item.user_review = reviews_by_product.get(item.product_id)

    context = {
        'purchased_products': purchased_products,
        'user_reviews': user_reviews,
        'reviewed_products': reviewed_products,
    }

    return render(request, 'accounts/my_reviews.html', context)


@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.order_by('-created_at').filter(user=request.user, is_ordered=True)
    
    context = {
        'orders': orders,
        
    }
    return render(request, 'accounts/my_orders.html', context)


@login_required(login_url='login')
def edit_profile(request):
    try:
        userprofile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        userprofile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Tu perfil ha sido actualizado')
            return redirect('edit_profile')
        else:
            # Agregar mensajes de error si la validación falla
            if not user_form.is_valid():
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            if not profile_form.is_valid():
                for field, errors in profile_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        
        user = Account.objects.get(username__exact=request.user.username)
        
        if new_password == confirm_password:
            sucess = user.check_password(current_password)
            if sucess:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Tu contraseña ha sido cambiada con éxito.')
                return redirect('change_password')
            else:
                messages.error(request, 'Tu contraseña actual no es correcta.')
                return redirect('change_password')
        else:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('change_password')
    
    return render(request, 'accounts/change_password.html')


@login_required(login_url='login')
def order_details(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for item in order_detail:
        subtotal += item.product_price
    
    context = {
        'order': order,
        'order_detail': order_detail,
        'subtotal': subtotal,
    }
    return render(request, 'accounts/order_details.html', context)

