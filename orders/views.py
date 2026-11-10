import datetime
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import OrderForm
from carts.models import CartItem
from .models import Order, Payment, OrderProduct
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from accounts.models import UserProfile



# Create your views here.
def payment(request):
    return render(request, 'orders/payment.html', {'stripe_configured': True})


@login_required
@require_POST
def stripe_create_checkout_session(request):
    order = Order.objects.filter(user=request.user, is_ordered=False).order_by('-created_at').first()
    if order is None:
        return JsonResponse({'error': 'No se encontró la orden pendiente.'}, status=404)

    try:
        session = stripe.checkout.Session.create(
            api_key=settings.STRIPE_SECRET_KEY,
            idempotency_key=f'checkout-order-{order.pk}',
            mode='payment',
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': f'Orden Calypso {order.order_number}'},
                    'unit_amount': int(order.order_total * 100),
                },
                'quantity': 1,
            }],
            client_reference_id=str(order.user_id),
            metadata={'order_id': str(order.pk), 'order_number': order.order_number},
            success_url=(
                request.build_absolute_uri(reverse('order_complete'))
                + '?session_id={CHECKOUT_SESSION_ID}'
            ),
            cancel_url=request.build_absolute_uri(reverse('place_order')),
        )
    except stripe.StripeError:
        return JsonResponse({'error': 'No se pudo iniciar el pago con Stripe.'}, status=502)

    return JsonResponse({'url': session.url})


def _finalize_stripe_session(checkout_session):
    if checkout_session.get('payment_status') != 'paid':
        raise ValueError('El pago todavía no está confirmado.')

    metadata = checkout_session.get('metadata') or {}
    order_id = metadata.get('order_id')
    if not order_id:
        raise ValueError('La sesión de Stripe no está asociada a una orden.')

    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if str(order.user_id) != str(checkout_session.get('client_reference_id')):
            raise ValueError('La sesión de Stripe no corresponde al usuario de la orden.')
        if (
            checkout_session.get('currency') != 'usd'
            or checkout_session.get('amount_total') != int(order.order_total * 100)
        ):
            raise ValueError('El total de Stripe no coincide con el total de la orden.')

        if order.is_ordered:
            if order.payment is None:
                raise ValueError('La orden pagada no tiene un registro de pago.')
            return order, order.payment

        payment = Payment.objects.create(
            user=order.user,
            payment_id=checkout_session.get('payment_intent') or checkout_session.get('id'),
            payment_method='Stripe',
            amount_paid=Decimal(checkout_session['amount_total']) / 100,
            status='COMPLETED',
        )
        order.payment = payment
        order.is_ordered = True
        order.status = 'Accepted'
        order.save(update_fields=['payment', 'is_ordered', 'status', 'updated_at'])

        cart_items = CartItem.objects.filter(user=order.user, is_active=True)
        for item in cart_items:
            OrderProduct.objects.create(
                order=order,
                payment=payment,
                user=order.user,
                product=item.product,
                product_price=item.product.price,
                ordered=True,
            )
            item.product.is_available = False
            item.product.save()

        message = render_to_string('orders/order_recieved_email.html', {
            'user': order.user,
            'order': order,
        })
        EmailMessage('Gracias por tu compra', message, to=[order.user.email]).send()
        cart_items.delete()

    return order, payment


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return JsonResponse({'error': 'Webhook de Stripe no configurado.'}, status=503)

    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.headers.get('Stripe-Signature', ''),
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return JsonResponse({'error': 'Firma de Stripe inválida.'}, status=400)

    if event['type'] == 'checkout.session.completed':
        try:
            _finalize_stripe_session(event['data']['object'])
        except (Order.DoesNotExist, ValueError):
            return JsonResponse({'error': 'No se pudo verificar la orden pagada.'}, status=400)

    return JsonResponse({'received': True})


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
                'stripe_configured': True,

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


@login_required
def order_complete(request):
    session_id = request.GET.get('session_id')

    try:
        if session_id:
            checkout_session = stripe.checkout.Session.retrieve(
                session_id,
                api_key=settings.STRIPE_SECRET_KEY,
            )
            order, payment = _finalize_stripe_session(checkout_session)
            if order.user_id != request.user.id:
                return redirect('home')
            order_number = order.order_number
            transID = payment.payment_id
        else:
            order_number = request.GET.get('order_number')
            transID = request.GET.get('payment_id')
            order = Order.objects.get(
                order_number=order_number,
                is_ordered=True,
                user=request.user,
            )
            payment = Payment.objects.get(payment_id=transID)

        ordered_products = OrderProduct.objects.filter(order_id=order.id)

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
    except (Payment.DoesNotExist, Order.DoesNotExist, ValueError, stripe.StripeError):
        return redirect('home')

