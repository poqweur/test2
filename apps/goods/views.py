from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.views.generic import View#导入视图父类
from django_redis import get_redis_connection
from order.models import OrderGoods
from goods.models import GoodsType,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner,GoodSKU,Goods
# Create your views here.
# def index(request):
#     '''首页'''
#     return render(request,'index.html')

class 首页视图(View):
    def get(self,request):
        '''显示'''
        #尝试从缓存中获取数据
        context=cache.get('index_page_data')

        if context is None:
            print('设置缓存了')
            #缓存中没有数据
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

            # 组织模板上下文
            context = {
                'types': types,
                'goods_banner': goods_banner,
                'promotion_banner': promotion_banner,
            }
            #设置缓存数据
            #缓存名称 缓存数据 过期时间
            cache.set('index_page_data',context,3600)
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
        context.update(cart_count=cart_count)
        return render(request,'index.html',context)

#/goods/商品id
class 商品详情(View):
    def get(self,request,sku_id):
        '''显示商品详情页面'''
        #根据sku_id获取商品的信息
        try:
            sku=GoodSKU.objects.get(id=sku_id)
            # print(sku.typeof_id)
        except GoodSKU.DoesNotExist:
            #商品不存在
            return redirect(reverse('goods:index'))
        #获取商品分类信息
        types=GoodsType.objects.all()
        #获取商品评论信息
        sku_orders=OrderGoods.objects.filter(sku=sku).exclude(comment='')[:30]
        #获取新品信息
        new_sku=GoodSKU.objects.filter(typeof=sku.typeof).order_by('-create_time')[:2]
        # print(new_sku)
        #获取商品其他规格
        same_spu_sku=GoodSKU.objects.filter(goods=sku.goods).exclude(id=sku_id)
        #判断用户是否登陆
        user = request.user
        cart_count=0
        if user.is_authenticated():
            #用户已登陆
            conn=get_redis_connection('default')
            cart_key='cart_%d'%user.id
            cart_count = conn.hlen(cart_key)
            #添加历史浏览记录
            conn=get_redis_connection('default')
            history_key='history_%d'%user.id
            #先尝试移除列表中对应元素
            conn.lrem(history_key,0,sku_id)
            #将sku_id插入到列表左侧
            conn.lpush(history_key,sku_id)
            #只保留用户浏览的最新5个商品
            conn.ltrim(history_key,0,4)
        #组织模板上下文
        context = {
            'sku': sku,
            'types': types,
            'sku_orders': sku_orders,
            'new_sku': new_sku,
            'same_spu_sku':same_spu_sku,
            'cart_count':cart_count,
        }
        #使用模板

        return render(request,'detail.html',context)

#restful api设计
#list/种类id/页码/排序方式
#/list/种类id/页码?sort=排序方式
class 商品列表(View):
    def get(self,request,type_id,page):
        '''显示详情页面'''
        try:
            typeof=GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            #种类不存在
            return redirect(reverse('goods:index'))

        #获取商品分类信息
        types=GoodsType.objects.all()
        #获取排序方式sort
        sort=request.GET.get('sort')
        #按照价格排序
        if sort == 'price':
            sot='price'
        #按照销量排序
        elif sort == 'hot':
            sot='-sales'
        #默认排序方式id
        else:
            sot='-id'
        #获取分类商品的信息
        sku=GoodSKU.objects.filter(typeof=typeof).order_by(sot)
        from  django.core.paginator import Paginator
        #对数据进行分页每页显示n个
        paginator=Paginator(sku,3)
        #处理页码
        try:
            page=int(page)
        except:
            #页码出错
            page=1
        if page > paginator.num_pages:
            page=1
        #获取page页的内容
        #返回的是page类的实例对象
        skus_page=paginator.page(page)

        #控制页码的列表最多在页面上显示5页
        #1.页码小于5页,显示所有页码
        #2.当前页属于前3页,显示前5页
        #当前页属于后3页,显示后5页
        #其他情况,显示当前页前两页和后两页
        num_pages=paginator.num_pages
        if num_pages <5:
            pages=range(1,num_pages+1)
        elif page <=3:
            pages=range(1,6)
        elif num_pages-page <=2:
            pages =range(num_pages-4,num_pages+1)
        else:
            pages=range(page-2,page+3)

        # 获取新品信息
        new_sku = GoodSKU.objects.filter(typeof=typeof).order_by('-create_time')[:2]

        # 判断用户是否登陆
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登陆
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
        #组织模板上线文
        context={
            'type':typeof,
            'types':types,
            'skus_page':skus_page,
            'new_sku':new_sku,
            'cart_count':cart_count,
            'sort':sort
        }

        return render(request,'list.html',context)







