from django.shortcuts import render, redirect
from fatherclass.Login import 自定义视图父类
from django.views.generic import View
from django.core.urlresolvers import reverse
from User.models import Address
from goods.models import GoodSKU
from django_redis import get_redis_connection
from django.http import JsonResponse
from order.models import OrderInfo, OrderGoods
from datetime import datetime


# Create your views here.
class 提交订单页面(自定义视图父类, View):
    def post(self, request):
        # 接收数据
        skulist = request.POST.getlist('sku_id')
        # 进行校验
        if not skulist:
            # 如果用户提交空的购物车跳转
            return redirect(reverse('cart:提交订单页面'))
        # 业务处理
        # 获取用户的地址信息
        addrs = Address.object.all()

        user = request.user
        conn = get_redis_connection()
        cart_key = 'cart_%d' % user.id
        total_count = 0
        total_price = 0
        skus = []
        # 遍历sku_ids获取每个商品的信息
        for sku_id in skulist:
            # 根据sku_id获取商品信息
            sku = GoodSKU.objects.get(id=sku_id)
            # 获取用户购买的商品的数据
            count = conn.hget(cart_key, sku_id)
            # 计算商品小计
            amount = sku.price * int(count)
            sku.amount = amount
            sku.count = count
            skus.append(sku)
            total_count += int(count)
            total_price += amount

        # 运费
        transit_price = 10  # 写死

        # 实际付款
        total_pay = total_price + transit_price
        # 组织上下文
        context = {
            'addrs': addrs,
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'total_pay': total_pay,
            'transit_price': transit_price
        }

        return render(request, 'place_order.html', context)


# 创建订单
# 前段发起ajax请求
# 前段传递:地址id 支付方式 用户要购买商品的id
# order/commit
# 用户每下一个订单,需要向订单信息表添加一条信息
# 向订单商品表中添加信息是,用户买了几件商品添加几条记录
#mysql事务:一组sql操作,要么都成功要么都失败
#高并发:防止用户下单重复
class 订单创建(View):
    def post(self, request):
        # 判断用户是否登陆
        user = request.user
        if not user.is_authenticated():
            # 用户为登陆
            return JsonResponse({'res': 0, 'errmsg': '用户为登陆'})
        # 接收数据
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        # 数据校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHOOS():
            return JsonResponse({'res': 2, 'errmsg': '非法支付方式'})
        # 校验地址
        try:
            addr = Address.object.get(id=addr_id)
        except:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址信息错误'})

        # 业务处理

        # 组织订单数据

        # 订单id:格式:20171122122930+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 10

        # 总金额和总数目
        total_count = 0
        total_price = 0
        # 向订单信息表中添加已条记录
        order = OrderInfo.objects.create(order_id=order_id,
                                         user=user,
                                         addr=addr,
                                         total_price=total_price,
                                         total_count=total_count,
                                         pay_method=pay_method,
                                         transit_price=transit_price
                                         )

        # 向订单商品表中添加信息时,用户买了及件商品,需要添加几条记录
        sku_ids = sku_ids.splite(',')
        conn = get_redis_connection()
        cart_key = 'cart_%d' % user.id
        for sku_id in sku_ids:
            try:
                sku = GoodSKU.objects.get(id=sku_id)
            except:
                return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
            # 从redis中获取用户需要购买的商品信息
            count = conn.hget(cart_key, sku_id)
            # 向订单表中添加已条记录
            OrderGoods.objects.create(
                order=order,
                sku=sku,
                count=count,
                price=sku.price
            )

            # 更新对应商品的库存和销量
            sku.stock -= int(count)
            sku.sales -= int(count)
            sku.save()
            # 累加订单中商品总数目和总金额
            total_count += int(count)
            amount = sku.price * int(count)
            total_price += amount
        # 更新订单信息表对应的总件数和总金额
        order.total_count = total_count
        order.total_price = total_price
        order.save()

        # 删除用户购物车中的相应记录
        conn.hdel(cart_key, *sku_ids)

        return JsonResponse({'res': 5, 'errmsg': '订单创建成功'})
