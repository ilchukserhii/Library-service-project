import os
import stripe
from dotenv import load_dotenv

from payments.models import Payment

load_dotenv()

client = stripe.StripeClient(os.getenv("STRIPE_KEY"))

def create_payment_for_borrowing(borrow):
        session = client.v1.checkout.sessions.create(
            params={
                "line_items": [{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Borrowing: {borrow.id}",
                        },
                        "unit_amount": int(borrow.calculate_price * 100),
                    },
                    "quantity": 1,
                }],
                "mode": "payment",
                "success_url": "http://localhost:8000/success",
                "cancel_url": "http://localhost:8000/cancel",
            },
        )
        Payment.objects.create(
          status="PENDING",
          type="PAYMENT",
          borrowings=borrow,
          session_url=session.url,
          session_id=session.id,
          money_to_pay=borrow.calculate_price
        )
