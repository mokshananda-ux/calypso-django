import datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .forms import OrderForm
from carts.models import CartItem
from .models import Order, Payment, OrderProduct
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from accounts.models import UserProfile



# Create your views here.
def payment(request):
    return render(request, 'orders/payment.html', {
        'paypal_client_id': settings.PAYPAL_CLIENT_ID,
    })


def _paypal_access_token():
    response = requests.post(
        f'{settings.PAYPAL_BASE_URL}/v1/oauth2/token',
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        headers={'Accept': 'application/json', 'Accept-Language': 'es_MX'},
        data={'grant_type': 'client_credentials'},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()['access_token']


@login_required
@require_POST
def paypal_create_order(request):
    order = Order.objects.filter(user=request.user, is_ordered=False).order_by('-created_at').first()
    if order is None:
        return JsonResponse({'error': 'No se encontró la orden pendiente.'}, status=404)

    try:
        token = _paypal_access_token()
        response = requests.post(
            f'{settings.PAYPAL_BASE_URL}/v2/checkout/orders',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            json={
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'reference_id': order.order_number,
                    'amount': {'currency_code': 'USD', 'value': f'{order.order_total:.2f}'},
                }],
            },
            timeout=15,
        )
        response.raise_for_status()
    except (requests.RequestException, KeyError) as error:
        return JsonResponse({'error': str(error)}, status=502)

    return JsonResponse({'id': response.json()['id']})


@login_required
@require_POST
def paypal_capture_order(request):
    paypal_order_id = request.POST.get('order_id')
    if not paypal_order_id:
        return JsonResponse({'error': 'ID de orden de PayPal es requerido.'}, status=400)

    order = Order.objects.filter(user=request.user, is_ordered=False).order_by('-created_at').first()
    if order is None:
        return JsonResponse({'error': 'No se encontró la orden pendiente.'}, status=404)

    try:
        token = _paypal_access_token()
        response = requests.post(
            f'{settings.PAYPAL_BASE_URL}/v2/checkout/orders/{paypal_order_id}/capture',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            timeout=15,
        )
        response.raise_for_status()
        paypal_data = response.json()
        capture = paypal_data['purchase_units'][0]['payments']['captures'][0]
    except (requests.RequestException, KeyError, IndexError) as error:
        return JsonResponse({'error': str(error)}, status=502)

    reference_id = paypal_data['purchase_units'][0].get('reference_id')
    amount = Decimal(capture['amount']['value'])
    if (
        paypal_data.get('status') != 'COMPLETED'
        or reference_id != order.order_number
        or amount != order.order_total
    ):
        return JsonResponse({'error': 'El pago de PayPal no pudo ser verificado.'}, status=400)

    with transaction.atomic():
        payment = Payment.objects.create(
            user=request.user,
            payment_id=capture['id'],
            payment_method='PayPal',
            amount_paid=amount,
            status=capture['status'],
        )
        order.payment = payment
        order.is_ordered = True
        order.status = 'Accepted'
        order.save(update_fields=['payment', 'is_ordered', 'status', 'updated_at'])

        # Mover items del carrito a OrderProducts
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save()

            # Marcar el producto como no disponible (productos únicos e irrepetibles)
            item.product.is_available = False
            item.product.save()

        # Enviar email de confirmación (fuera del bucle para enviar solo un email)
        mail_subject = 'Gracias por tu compra'
        message = render_to_string('orders/order_recieved_email.html', {
            'user': request.user,
            'order': order,
        })
        to_email = request.user.email
        send_email = EmailMessage(mail_subject, message, to=[to_email])
        send_email.send()

        # Limpiar el carrito después de la compra
        cart_items.delete()

    return JsonResponse({'status': 'COMPLETED', 'order_number': order.order_number, 'payment_id': payment.payment_id})


@login_required(login_url='login')
def place_order(request):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    total = 0
    tax = 0

    for cart_item in cart_items:
        total += cart_item.product.price


    # Calculate tax and grand total even if cart does not exist or is empty
    tax = (2 * total) / 100
    grand_total = total + tax

    # Obtener perfil del usuario para precargar datos
    try:
        userprofile = UserProfile.objects.get(user=current_user)
    except UserProfile.DoesNotExist:
        userprofile = None

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.zip_code = form.cleaned_data['zip_code']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            yr = int(datetime.date.today().strftime('%Y'))
            mt = int(datetime.date.today().strftime('%m'))
            dt = int(datetime.date.today().strftime('%d'))
            d = datetime.datetime(yr, mt, dt)
            current_date = d.strftime('%Y%m%d')
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context= {
                'order':order,
                'cart_items':cart_items,
                'total':total,
                'grand_total':grand_total,
                'tax':tax,
                'paypal_client_id': settings.PAYPAL_CLIENT_ID,

            }
            return render(request, 'orders/payment.html', context)

    else:
        # Precargar datos del usuario en el formulario
        initial_data = {
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'email': current_user.email,
            'phone': current_user.phone_number,
        }

        if userprofile:
            initial_data.update({
                'address_line_1': userprofile.address_line_1,
                'city': userprofile.city,
                'state': userprofile.state,
                'zip_code': userprofile.zip_code,
            })

        form = OrderForm(initial=initial_data)

        context = {
            'form': form,
            'cart_items': cart_items,
            'total': total,
            'tax': tax,
            'grand_total': grand_total,
        }
        return render(request, 'store/checkout.html', context)


def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(payment_id=transID)

        # Calcular el subtotal
        subtotal = 0
        for item in ordered_products:
            subtotal += item.product_price

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'transID': transID,
            'order_number': order_number,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

