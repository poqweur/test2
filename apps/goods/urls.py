from django.conf.urls import url
# from goods import views
from goods.views import 首页视图
urlpatterns=[
    # url(r'^',views.index,name='index')
    url(r'^$',首页视图.as_view(),name='index'),
]