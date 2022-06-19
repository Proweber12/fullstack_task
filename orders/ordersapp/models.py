import datetime

from django.db import models


class Orders(models.Model):
    order_number = models.PositiveIntegerField(verbose_name="заказ №", blank=True, null=False, default=0)
    price_usd = models.PositiveIntegerField(verbose_name="стоимость,$", blank=True, null=False, default=0)
    delivery_time = models.DateField(verbose_name="срок поставки", blank=True, null=False,
                                     default=datetime.date(1970, 1, 1))
    price_rub = models.PositiveIntegerField(verbose_name="стоимость,₽", blank=True, null=False, default=0)
