from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from django.template import loader,RequestContext
import os
import time
#加载django文件
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Fresheveryday.settings")
import django
#启动django初始化
django.setup()
from django_redis import get_redis_connection
from goods.models import GoodsType,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner

#创建celery对象,指定中间人路径
app=Celery('celery_tasks.tasks',broker='redis://127.0.0.1:6379/5')

#创建任务函数
@app.task
def send_register_actie_email(to_email,username,token):
    email_title = '天天生鲜欢迎信息'
    email_body = ''
    send = settings.EMAIL_FROM
    receive=[to_email]
    html='<h1>%s,欢迎你成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://192.168.109.131:8000/user/active/%s">http://192.168.109.131:8000/user/active/%s</a>'%(username,token,to_email)
    time.sleep(5)
    send_mail(email_title, email_body, send, receive,html_message=html)

@app.task
def generate_static_index_html():
    '''生成静态页面'''
    # 获取商品的分类信息
    types = GoodsType.objects.all()
    # 获取首页轮播商品细细
    goods_banner = IndexGoodsBanner.objects.all().order_by('index')
    # 获取首页促销活动信息
    promotion_banner = IndexPromotionBanner.objects.all().order_by('index')
    # 获取首页分类商品展示信息
    for type in types:
        image_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        title_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        # 给对象动态增加属性,分别保存首页展示的图片商品信息和标题信息
        type.image_banner = image_banner
        type.title_banner = title_banner
    # 获取购物车条数
    cart_count = 0
    # 组织模板上下文
    context = {
        'types': types,
        'goods_banner': goods_banner,
        'promotion_banner': promotion_banner,
        'cart_count': cart_count
    }
    #1.加载模板文件,返回一个模板对象
    temp=loader.get_template('static_index.html')
    #2.定义模板上下文,给模板文件传数据
    # context=RequestContext(request,context)
    #3.模板渲染
    static_html=temp.render(context)

    #生成静态文件
    save_path=os.path.join(settings.BASE_DIR,'static/index.html')
    with open(save_path,'w') as f:
        f.write(static_html)