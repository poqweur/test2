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
        user = request.user
        # 判断用户是否登陆
        if user.is_authenticated():
            # 接收数据
            sku_id = request.POST.get('sku_id')
            count = request.POST.get('count')
            # 数据校验
            if all([sku_id, count]):
                # 校验商品的数目
                try:
                    count = int(count)
                except:
                    # 商品数目不错
                    return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
                # 校验商品是否存在
                try:
                    sku = GoodSKU.objects.get(id=sku_id)
                except:
                    return JsonResponse({'res': 3, 'errmsg': '商品不存在'})
                # 业务处理:添加购物车记录
                conn = get_redis_connection('default')
                cart_key = 'cart_%d' % user.id
                # 先尝试获取cart_key中sku_id的值
                sku_count = conn.hget(cart_key, sku_id)
                if sku_count:
                    # 如果购物车中商品已存在,数目需要累加
                    count += int(sku_count)
                # 校验商品的库存
                if count > sku.stock:
                    return JsonResponse({'res': 4, 'errmsg': '商品库存补足'})
                # 添加记录
                conn.hset(cart_key, sku_id, count)
                # 获取用户购物车的条目书
                cart_count = conn.hlen(cart_key)
                # 返回应答
                return JsonResponse({'res': 5, 'errmsg': '添加成功', 'cart_count': cart_count})
            else:
                return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        else:
            return JsonResponse({'res': 0, 'errmsg': '请先登陆'})


# /cart/
class 购物车页面显示(自定义视图父类, View):
    def get(self, request):
        # 获取登录用户
        user = request.user
        # 获取用户购物车中的商品信息
        conn = get_redis_connection()
        cart_key = 'cart_%d' % user.id
        # {'商品id':商品数目,....}
        cart_dict = conn.hgetall(cart_key)

        skus = []
        # 分别保存用户购物车中商品的总件数和总价格
        total_count = 0
        total_price = 0
        for sku_id, count in cart_dict.items():
            # 根据sku_id获取商品的信息
            sku = GoodSKU.objects.get(id=sku_id)
            # 计算商品的小计
            amount = sku.price * int(count)
            # 动态给sku对象增加一个属性amount
            sku.amount = amount
            # 动态给sku对象增加一个属性count
            sku.count = count
            # 添加
            skus.append(sku)
            # 累加计算商品的总件数和总价格
            total_count += int(count)
            total_price += amount
        # 组织上下文
        context = {
            'total_count': total_count,
            'total_price': total_price,
            'skus': skus
        }

        return render(request, 'cart.html', context)


# 更新记录
# 采用ajax post请求
# 前段需要传递的参数:商品id>sku_id商品数量:count
# cart/update
class 购物车记录更新(View):
    def post(self, request):
        user = request.user
        # 判断用户是否登陆
        if not user.is_authenticated():
            #用户每登陆
            return JsonResponse({'res': 0, 'errmsg': '请先登陆'})
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 进行校验
        if not all([sku_id, count]):
            return JsonResponse({'res':1,'errmsg':'数据不完整'})
        # 校验商品的数目
        try:
            count = int(count)
        except Exception as e:
            # 商品数目出错
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
        # 校验商品是否存在
        try:
            sku = GoodSKU.objects.get(id=sku_id)
        except GoodSKU.DoesNotExist:
            #商品不存在
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})
        # 业务处理:购物记录更新
        conn = get_redis_connection()
        cart_key = 'cart_%d' % user.id
        #校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存补足'})
        # 更新
        conn.hset(cart_key, sku_id, count)
        #获取购物车中全部商品的总件数
        total_count=0
        vals=conn.hvals(cart_key)
        for val in vals:
            total_count+=int(val)
        # 返回应答
        return JsonResponse({'res': 5, 'errmsg': '更新成功','total_count':total_count})


# 删除购物车记录
#ajax post请求
#前段传递的参数:商品id
class 购物车记录删除(View):
    def post(self, request):
        #判断用户是否登陆
        user=request.user
        if not user.is_authenticated():
            #用户没登陆
            return JsonResponse({'res':0,'errmsg':'请先登陆'})
        # 接收参数
        sku_id=request.POST.get('sku_id')
        # 校验参数
        if not sku_id:
            return JsonResponse({'res':1,'errmsg':'参数不完整'})
        #校验商品是否存在
        try:
            sku=GoodSKU.objects.get(id=sku_id)
        except GoodSKU.DoesNotExist:
            #商品不存在
            return JsonResponse({'res':2,'errmsg':'商品不存在'})
        # 业务处理:删除购物车记录
        conn=get_redis_connection('default')
        cart_key='cart_%d'%user.id
        #删除:从cart_key对应的元素中删除sku_id
        conn.hdel(cart_key,sku_id)
        # 获取购物车中全部商品的总件数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)
        # 返回应答
        return JsonResponse({'res':3,'total_count':total_count,'message':'删除成功'})
