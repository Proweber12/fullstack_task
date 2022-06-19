from django.shortcuts import render
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from .models import Orders
from .serializers import OrdersBaseModelSerializer


class OrdersCustomViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Orders.objects.all()
    serializer_class = OrdersBaseModelSerializer
