import os
import stripe
from django.urls import reverse
from dotenv import load_dotenv

from payments.models import Payment

load_dotenv()

client = stripe.StripeClient(os.getenv("STRIPE_KEY"))


def create_payment_for_borrowing(borrow, request):
    amount = borrow.calculate_price
    payment_type = "PAYMENT"
    create_stripe_payment_session(borrow, request, amount, payment_type)


def create_fine_payment_for_borrowing(borrow, request):
    amount = borrow.calculate_fine_price
    payment_type = "FINE"
    create_stripe_payment_session(borrow, request, amount, payment_type)


def create_stripe_payment_session(borrow, request, amount, payment_type):
    success_url = request.build_absolute_uri(
        reverse("payments:payments-success")
    )
    cancel_url = request.build_absolute_uri(
        reverse("payments:payments-cancel")
    )
    session = client.v1.checkout.sessions.create(
        params={
            "line_items": [{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Borrowing: {borrow.id}",
                    },
                    "unit_amount": int(amount * 100),
                },
                "quantity": 1,
            }],
            "mode": "payment",
            "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": cancel_url,
        },
    )
    Payment.objects.create(
      status="PENDING",
      type=payment_type,
      borrowings=borrow,
      session_url=session.url,
      session_id=session.id,
      money_to_pay=amount
    )
