from django.conf.urls import url
# from goods import views
from goods.views import 首页视图,商品详情,商品列表
urlpatterns=[
    # url(r'^',views.index,name='index')
    url(r'^$',首页视图.as_view(),name='index'),
    url(r'^goods/(?P<sku_id>\d+)',商品详情.as_view(),name='detail'),
    url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)',商品列表.as_view(),name='list'),
]