from rest_framework.serializers import ModelSerializer

from .models import Orders


class OrdersBaseModelSerializer(ModelSerializer):
    class Meta:
        model = Orders
        fields = (
            "id",
            "order_number",
            "price_usd",
            "delivery_time",
            "price_rub",
        )
