from django.contrib.auth.views import login_required
#@login_required,装饰器可以装饰给视图函数,类只能嵌套函数login_required(视图函数),或类继承.
# 如果用户没有登入，则重定向到settings.LOGIN_URL
class 自定义视图父类(object):
    @classmethod
    def as_view(cls,**initkwargs):
        #首先调用父类的as_view
        view=super().as_view(**initkwargs)
        return login_required(view)