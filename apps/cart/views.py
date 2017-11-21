from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from goods.models import GoodSKU
from django_redis import get_redis_connection
from fatherclass.Login import 自定义视图父类
# Create your views here.
# 如果涉及到数据的修改,采用post方式
# 如果涉及到数据的获取,采用get方式
class 购物车记录添加(View):
    def post(self, request):
        user=request.user
        #判断用户是否登陆
        if user.is_authenticated():
            #接收数据
            sku_id=request.POST.get('sku_id')
            count=request.POST.get('count')
            #数据校验
            if all([sku_id,count]):
                #校验商品的数目
                try:
                    count=int(count)
                except:
                    #商品数目不错
                    return JsonResponse({'res':2,'errmsg':'商品数目出错'})
                #校验商品是否存在
                try:
                    sku=GoodSKU.objects.get(id=sku_id)
                except:
                    return JsonResponse({'res':3,'errmsg':'商品不存在'})
                #业务处理:添加购物车记录
                conn=get_redis_connection('default')
                cart_key='cart_%d'%user.id
                #先尝试获取cart_key中sku_id的值
                sku_count=conn.hget(cart_key,sku_id)
                if sku_count:
                    #如果购物车中商品已存在,数目需要累加
                    count+=int(sku_count)
                #校验商品的库存
                if count>sku.stock:
                    return JsonResponse({'res':4,'errmsg':'商品库存补足'})
                #添加记录
                conn.hset(cart_key,sku_id,count)
                #获取用户购物车的条目书
                cart_count=conn.hlen(cart_key)
                #返回应答
                return JsonResponse({'res':5,'errmsg':'添加成功','cart_count':cart_count})
            else:
                return JsonResponse({'res':1,'errmsg':'数据不完整'})
        else:
            return JsonResponse({'res':0,'errmsg':'请先登陆'})

#/cart/
class 购物车页面显示(自定义视图父类,View):
    def get(self,request):
        #获取登录用户
        user=request.user
        #获取用户购物车中的商品信息
        conn=get_redis_connection()
        cart_key='cart_%d'%user.id
        #{'商品id':商品数目,....}
        cart_dict=conn.hgetall(cart_key)

        skus=[]
        #分别保存用户购物车中商品的总件数和总价格
        total_count=0
        total_price=0
        for sku_id,count in cart_dict.items():
            #根据sku_id获取商品的信息
            sku=GoodSKU.objects.get(id=sku_id)
            #计算商品的小计
            amount=sku.price*int(count)
            #动态给sku对象增加一个属性amount
            sku.amount=amount
            #动态给sku对象增加一个属性count
            sku.count=count
            #添加
            skus.append(sku)
            #累加计算商品的总件数和总价格
            total_count+=int(count)
            total_price+=amount
        #组织上下文
        context={
            'total_count':total_count,
            'total_price':total_price,
            'skus':skus
        }

        return render(request,'cart.html',context)