from django.contrib import admin

# Register your models here.
from order.models import OrderInfo


admin.site.register(OrderInfo)