from django.conf.urls import url
from cart.views import 购物车记录删除,购物车记录添加,购物车页面显示,购物车记录更新

urlpatterns = [
    url(r'^add$',购物车记录添加.as_view(),name='add'),
    url(r'^$',购物车页面显示.as_view(),name='购物车页面显示'),
    url(r'^update$',购物车记录更新.as_view(),name='购物车记录更新'),
    url(r'^delete$',购物车记录删除.as_view(),name='购物车记录删除')
]