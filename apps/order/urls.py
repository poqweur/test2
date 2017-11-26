from django.conf.urls import url
from order.views import 订单评论,查询订单支付结果,提交订单页面,订单创建,订单支付

urlpatterns = [
    url(r'^place$',提交订单页面.as_view(),name='place'),
    url(r'^commit$',订单创建.as_view(),name='commit'),
    url(r'^pay$',订单支付.as_view(),name='pay'),
    url(r'^check$',查询订单支付结果.as_view(),name='check'),
    url(r'^comment/(?P<order_id>.+)',订单评论.as_view(),name='comment')

]