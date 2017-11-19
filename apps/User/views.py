from django.shortcuts import render,redirect#重定向
from django.core.urlresolvers import reverse#重定向反向解析
from django.http import HttpResponse
from django.conf import settings
from django_redis import get_redis_connection#django包提供的redis连接对象
from django.views.generic import View#类视图调用父类
from celery_tasks.tasks import send_register_actie_email#导入队列类发送邮件
import re
from itsdangerous import TimedJSONWebSignatureSerializer,SignatureExpired#对用户信息加密和解密
# from User.models import GoodInfo
from User.models import User,Address
from goods.models import GoodSKU
from django.core.mail import send_mail,send_mass_mail
from fatherclass.Login import 自定义视图父类

#django提供的user添加方法
# from django.contrib.auth.models import User
# 判断是否存在
from django.contrib.auth import authenticate,login,logout

def 测试(request):
    # user=User.objects.create_user('wjy','123@163.com','123')#添加用户
    # user=authenticate(username='python',password='123')#验证用户
    # if user:
    #     print(user)
    # else:
    #     print('不存在')
    #发送邮件
    email_title='标题'
    email_body='内容'
    email='1149447019@qq.com'
    send_mail(email_title,'','我自己<1149447019@qq.com>' ,[email])
    return HttpResponse('ok')



# def 富文本(request):
#     # return render(request, 'test/test.html')
#     return render(request,'test/editor.html')
#
# def 展示富文本(request):
#     goods=request.POST.get('gcontent')
#     # con=GoodInfo.objects.get('gcontent')
#     # pinjie={'goods':goods,'con':con}
#     # print(goods)
#     context={'goods':goods}
#     return render(request,'test/test.html',context)

def 展示用户登陆(request):
    # 只判断是否有cookie
    if 'uname' in request.COOKIES:
        #如果有cookie信息就记住用户名
        name = request.COOKIES['uname']
        checked = 'checked'
    else:
        name = ''
        checked = ''
    return render(request,'test/admin.html',{'name':name,'checked':checked})

def index(request):
    return render(request,'test/index.html')

def 校验用户登陆(request):
    uname=request.POST.get('uname')
    upassword=request.POST.get('upassword')
    remember=request.POST.get('remember')
    # print(remember)
    if uname=='python' and upassword == '123':
        resopnse = redirect('/user/index')
        if remember == 'on':
            #如果用户选择记住密码就把cookie写入浏览器
            resopnse.set_cookie('uname',uname,max_age=7*24*3600)
        else:
            #否则就清除cookie信息
            resopnse.delete_cookie('uname')
        #记录用户登录状态
        #只有session中有islogin就认为用户已登陆
        request.session['islogin']='yes'
        #写入session
        request.session['uname']=uname
        return resopnse
    else:
        return redirect('/user/addmin')

def 装饰器(函数):
    #装饰器中判断用户是否登陆
    def wrapper(requset,*args,**kwargs):
        print(requset.session.has_key('islogin'))
        if requset.session.has_key('islogin'):
            return 函数(requset,*args,**kwargs)
        else:
            return redirect('/user/addmin')
    return wrapper

@装饰器
def 用户页面(request):
    return render(request,'test/user.html',{'name':request.session['uname']})

def 退出登陆(request):
    #删除session信息
    request.session.flush()
    return redirect('/user/addmin')

class 注册类(View):
    def post(self,request):
        name = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email=request.POST.get('email')
        check=request.POST.get('allow')
        print(check)
        if all([name,password,email]):#判断用户名,密码,邮箱是否有值
            if re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):#判断邮箱是否合法
                if check:#判断是否记住同意
                    #如果符合以上标准进行注册业务
                    try:
                        对象=User.objects.get(username=name)
                    except User.DoesNotExist:
                        对象=None
                    if 对象:
                        return render(request,'register.html',{'error':'用户已存在'})
                    对象=User.objects.create_user(name,email,password)
                    对象.is_active=0#未激活
                    对象.save()
                    身份信息加密=TimedJSONWebSignatureSerializer(settings.SECRET_KEY,3600)#加密(加密方式,时间秒)
                    info={'id':对象.id}
                    token=身份信息加密.dumps(info).decode()#需要加密的信息info
                    send_register_actie_email.delay(email,name,token)#使用celery发送邮件
                    return redirect(reverse('goods:index'))
        return render(request,'register.html',{'error':'信息填写有误'})

    def get(self,request):
        return render(request,'register.html')

class 激活账户(View):
    def get(self,request,token):
        身份信息加密=TimedJSONWebSignatureSerializer(settings.SECRET_KEY,3600)
        try:
            info=身份信息加密.loads(token)
            user_id=info['id']
            user=User.objects.get(id=user_id)
            user.is_active=1
            user.save()
            return redirect(reverse('User:登录'))
        except Exception as e: #SignatureExpired:
            print(e)
            return HttpResponse('激活已失效')

class 登录(View):
    def get(self,request):
        if 'username' in request.COOKIES:
            username=request.COOKIES.get('username')
            checked='checked'
        else:
            username=''
            checked=''
        return render(request,'login.html',{'username':username,'checked':checked})

    def post(self,request):
        username=request.POST.get('username')
        password=request.POST.get('pwd')
        if all([username,password]):
            #登陆验证
            user=authenticate(username=username,password=password)
            print(user)
            if user:
                #用户密码正确
                if user.is_active:
                    #记住登陆状态
                    login(request,user)#写入cookie
                    #跳转next如果没有就到首页
                    resopnse=redirect(request.GET.get('next',reverse('goods:index')))

                    #是否需要记住用户名
                    remember=request.POST.get('remember')
                    if remember=='on':
                        #如果选择记住用户名,则把用户名写入cookie信息
                        resopnse.set_cookie('username',username)
                    else:
                        resopnse.delete_cookie('username')
                    return resopnse
                else:
                    return render(request,'login.html',{'error':'账户未激活'})
            else:
                return render(request,'login.html',{'error':'用户名或密码错误'})
        else:
            return render(request, 'login.html', {'error': '数据不完整'})


class 退出(View):
    def get(self,request):
        #清楚session信息
        logout(request)
        #跳转到首页
        return redirect(reverse('goods:index'))

class userinfoview(自定义视图父类,View):
    #用户浏览过商品添加浏览记录
    def get(self,request):
        #request对象本身就有user属性
        user=request.user
        address=Address.object.get_default_address(user)

        #用户浏览记录
        #获取redis连接对象
        conn=get_redis_connection()
        list_key='history_%d'%user.id

        #从redis中获取用户浏览的商品id
        sku_ids=conn.lrange(list_key,0,4)

        #遍历查询用户历史浏览器的商品信息,追加到goods_li列表中
        goods_li=[]
        for i in sku_ids:
            goods=GoodSKU.objects.get(id=i)
            goods_li.append(goods)
        #组织模板上下文
        context={'page':'user','address':address,'goods_li':goods_li}
        #django还会把request.user转给模板文件
        return render(request, 'user_center_info.html', context)

class userorderview(自定义视图父类,View):
    '''用户中心-订单'''
    def get(self,request):
        '''显示'''
        #获取用混得订单信息

        return render(request,'user_center_order.html',{'page':'order'})

class addressview(自定义视图父类,View):
    '''用户中心-地址页'''
    def get(self,request):
        user=request.user

        address=Address.object.get_default_address(user=user)
        return render(request,'user_center_site.html',{'page':'address','address':address})

    def post(self,request):
        '''地址的添加'''
        receive=request.POST.get('receive')
        addr=request.POST.get('addr')
        邮编=request.POST.get('zip_code')
        phone=request.POST.get('phone')
        print(receive,addr,phone)
        #数据检验
        if all([receive,addr,phone]):
            #联系方式校验
            if re.match(r'^1[3|4|5|7|8][0-9]{9}$',phone):
                user=request.user
                address=Address.object.get_default_address(user=user)
                if address:
                    is_default=False
                else:
                    is_default=True
                #添加地址
                Address.object.create(
                    user=user,
                    receiver=receive,
                    addr=addr,
                    zip_code=邮编,
                    phone=phone,
                    is_default=is_default
                )
                return redirect(reverse('User:addressview'))
            return render(request, 'user_center_site.html', {'errmsg':'联系方式不正确'})
        return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})