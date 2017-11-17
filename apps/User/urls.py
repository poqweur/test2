from django.conf.urls import url
from django.contrib.auth.decorators import login_required#如果用户没有登入，则重定向到settings.LOGIN_URL
from apps.User import views
from apps.User.views import 注册类,激活账户,登录,userinfoview,userorderview,addressview,退出

urlpatterns=[
    # url(r'^test/', views.富文本),
    # url(r'^show/',views.展示富文本),
    # url(r'^addmin',views.展示用户登陆),
    # url(r'^jiaoyan',views.校验用户登陆),
    # url(r'^user1$',views.用户页面),
    # url(r'^index',views.index),
    # url(r'^ceshi',views.测试),
    url(r'^register',注册类.as_view(),name='注册类'),
    url(r'^active/(?P<token>.*)',激活账户.as_view(),name='激活账户'),
    url(r'^login',登录.as_view(),name='登录'),
    url(r'^user',userinfoview.as_view(),name='userinfoview'),
    url(r'^order',userorderview.as_view(),name='userorderview'),
    url(r'^addr',addressview.as_view(),name='addressview'),
    url(r'^out',退出.as_view(),name='退出')
]