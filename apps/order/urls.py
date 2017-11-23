from django.conf.urls import url
from order.views import 提交订单页面,订单创建

urlpatterns = [
    url(r'^place$',提交订单页面.as_view(),name='place'),
    url(r'^commit$',订单创建.as_view(),name='commit')
]