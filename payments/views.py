import os

import stripe
from dotenv import load_dotenv
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from payments.models import Payment
from payments.serializers import (
    PaymentListSerializer,
    PaymentDetailSerializer
)


load_dotenv()

client = stripe.StripeClient(os.getenv("STRIPE_KEY"))


class PaymentsView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Payment.objects.all()
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        return PaymentDetailSerializer

    def get_queryset(self):
        queryset = Payment.objects.filter(
            borrowings__user=self.request.user
        )

        if self.request.user.is_staff:
            queryset = Payment.objects.all()

        return queryset

    @extend_schema(
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Payment status",
            )
        },
        description=(
                "If payment was successful, "
                "payment status will be set to 'PAID'"
        )
    )
    @action(detail=False, methods=["get"])
    def success(self, request):
        session_id = request.query_params.get("session_id")

        session = client.v1.checkout.sessions.retrieve(session_id)

        payment = Payment.objects.get(session_id=session_id)

        if session.payment_status == "paid":
            payment.status = "PAID"
            payment.save()

        return Response({"status": payment.status})

    @extend_schema(
        request=None,
        responses={
            OpenApiResponse(
                description=(
                        "Payment can be made later. "
                        "Session is available for 24 hours."
                )
            )
        },
        description=(
                "If payment was canceled it "
                "will be available for 24 hours."
        )
    )
    @action(detail=False, methods=["get"])
    def cancel(self, request):
        return Response(
            {
                "detail": (
                    "Payment can be made later. "
                    "Session is available for 24 hours."
                )
            }
        )
