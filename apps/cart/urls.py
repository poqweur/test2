from django.conf.urls import url
from cart.views import 购物车记录添加,购物车页面显示

urlpatterns = [
    url(r'^add$',购物车记录添加.as_view(),name='add'),
    url(r'^$',购物车页面显示.as_view(),name='购物车页面显示')
]