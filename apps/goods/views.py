from django.shortcuts import render
from django.views.generic import View#导入视图父类
from django_redis import get_redis_connection
from goods.models import GoodsType,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner
# Create your views here.
# def index(request):
#     '''首页'''
#     return render(request,'index.html')

class 首页视图(View):
    def get(self,request):
        '''显示'''
        #获取商品的分类信息
        types=GoodsType.objects.all()
        #获取首页轮播商品细细
        goods_banner=IndexGoodsBanner.objects.all().order_by('index')
        #获取首页促销活动信息
        promotion_banner=IndexPromotionBanner.objects.all().order_by('index')
        #获取首页分类商品展示信息
        for type in types:
            image_banner=IndexTypeGoodsBanner.objects.filter(type=type,display_type=1).order_by('index')
            title_banner=IndexTypeGoodsBanner.objects.filter(type=type,display_type=0).order_by('index')
            #给对象动态增加属性,分别保存首页展示的图片商品信息和标题信息
            type.image_banner=image_banner
            type.title_banner=title_banner
        #获取购物车条数
        cart_count=0
        #判断用户是否登陆
        user=request.user
        if user.is_authenticated():
            #用户已登陆
            conn=get_redis_connection('default')
            cart_key='cart_%d'%user.id
            #redis数据库查询用户购物车种类数量
            cart_count=conn.hlen(cart_key)
        #组织模板上下文
        context={
            'types':types,
            'goods_banner':goods_banner,
            'promotion_banner':promotion_banner,
            'cart_count':cart_count
        }
        return render(request,'index.html',context)