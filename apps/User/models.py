from django.db import models
#继承django的用户模型
from django.contrib.auth.models import AbstractUser# as django用户模型
from fatherclass.basemodel import 新建父类
#引用富文本中的HTML字段方法
# from tinymce.models import HTMLField
# from django.contrib.auth import models,backends#重写user模型

#重写user模型
# class user(models.Model):
    #user模型
    # name=models.OneToOneField()

    # def create_user(self,email,date_of_birth,password=None):
    #     #重写添加数据的方法
    #     pass

#重写认证后台
# class 后台认证(backends.ModelBackend):
#
#     def authenticate(self, username=None, password=None, **kwargs):
#         pass

# class BaseModel(models.Model):
#     '''模型类抽象基类'''
#     create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
#     update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
#     is_delete = models.BooleanField(default=False, verbose_name='删除标记')
#
#     class Meta:
#         # 说明是一个抽象模型类
#         abstract = True


# class GoodInfo(models.Model):
#     name=HTMLField(verbose_name='富文本')
#     class Meta:
#         db_table='富文本'

class User(AbstractUser,新建父类):
    '''用户模型类'''
    # object=models.Manager()
    class Meta:
        db_table='df_user'
        verbose_name='用户'
        verbose_name_plural=verbose_name#不以复数显示

class addressmanager(models.Manager):
    '''地址模型管理器'''
    def get_default_address(self,user):
        #获取用户默认的收货地址
        #获取self对象所在模型类
        try:
            address=self.get(user=user,is_default=True)
        except self.model.DoesNotExist:
            #没有默认地址
            address=None
        return address

class Address(新建父类):
    '''地址模型类'''
    user=models.ForeignKey('User',verbose_name='所属账户')
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, null=True, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    object=addressmanager()

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name

