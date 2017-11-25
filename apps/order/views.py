from django.shortcuts import render, redirect
from fatherclass.Login import 自定义视图父类
from django.views.generic import View
from django.core.urlresolvers import reverse
from User.models import Address
from goods.models import GoodSKU
from django_redis import get_redis_connection
from django.http import JsonResponse
from order.models import OrderInfo, OrderGoods
from django.db import transaction#mysql事务装饰器
from datetime import datetime
from alipay import AliPay
from django.conf import settings
import os


# Create your views here.
class 提交订单页面(自定义视图父类, View):
    def post(self, request):
        # 接收数据
        skulist = request.POST.getlist('sku_ids')
        print(skulist)
        # 进行校验
        if not skulist:
            # 如果用户提交空的购物车跳转
            return redirect(reverse('cart:购物车页面显示'))
        # 业务处理
        # 获取用户的地址信息
        addrs = Address.object.all()

        user = request.user
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        #保存总数量和总金额
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
            # print(sku.price)
            # print(count)
            amount = sku.price * int(count)
            sku.amount = amount
            sku.count = count
            skus.append(sku)
            #总件数
            total_count += int(count)
            #总金额
            total_price += amount

        # 运费
        transit_price = 10  # 写死

        # 实际付款
        total_pay = total_price + transit_price
        #商品id列表转化成字符串
        sku_ids=','.join(skulist)
        # 组织上下文
        context = {
            'addrs': addrs,
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'total_pay': total_pay,
            'transit_price': transit_price,
            'sku_ids':sku_ids
        }

        return render(request, 'place_order.html', context)


# 创建订单
# 前段发起ajax请求
# 前段传递:地址id->addr_id 支付方式pay_method 用户要购买商品的id->sku_ids
# order/commit
# 用户每下一个订单,需要向订单信息表添加一条信息
# 向订单商品表中添加信息是,用户买了几件商品添加几条记录
#mysql事务:一组sql操作,要么都成功要么都失败
#高并发:防止用户下单重复
class 订单创建(View):
    @transaction.atomic#事务开始
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
        print(addr_id)
        print(type(addr_id))
        print(pay_method)
        print(sku_ids)
        # 数据校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法支付方式'})

        # 校验地址
        try:
            addr = Address.object.get(id=addr_id)
        except:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址信息错误'})

        # 业务处理
        # 组织订单数据
        #todo: 订单id:格式:20171122122930+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 10

        # 总金额和总数目
        total_count = 0
        total_price = 0
        #todo:设置保存点
        save_id=transaction.savepoint()
        try:
            #todo: 向订单信息表中添加已条记录
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             total_price=total_price,
                                             total_count=total_count,
                                             pay_method=pay_method,
                                             transit_price=transit_price
                                             )

            # todo:向订单商品表中添加信息时,用户买了几件商品,需要添加几条记录
            skulist = sku_ids.split(',')
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            print(cart_key)
            for sku_id in skulist:
                for i in range(3):
                    try:
                        # todo:悲观锁select_for_update()
                        #sku = GoodSKU.objects.select_for_update().get(id=sku_id)
                        sku = GoodSKU.objects.get(id=sku_id)
                    except GoodSKU.DoesNotExist:
                        #商品不存在
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
                    # 从redis中获取用户需要购买的商品信息
                    count = conn.hget(cart_key, sku_id)
                    # 乐观锁
                    # 更新时做判断,判断更新时查到的库存是否一致
                    # todo:更新是做判断
                    origin_stock = sku.stock
                    news_stock = origin_stock - int(count)
                    news_sales = sku.sales + int(count)

                    #判断商品的库存
                    if int(count)>sku.stock:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res':6,'errmsg':'商品库存不足'})
                    # 返回受影响的次数
                    res = GoodSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=news_stock,
                                                                                       sales=news_sales)
                    if res == 0:
                        # 尝试3次
                        if i == 2:
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': 8, 'errmsg': '下单失败2'})
                        continue
                    # todo:向订单表中添加已条记录
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=count,
                        price=sku.price
                    )

                    # 更新对应商品的库存和销量
                    sku.stock -= int(count)
                    sku.sales += int(count)
                    sku.save()
                    # 累加订单中商品总数目和总金额
                    total_count += int(count)
                    amount = sku.price * int(count)
                    total_price += amount
                    break

                #todo: 更新订单信息表对应的总件数和总金额
                order.total_count = total_count
                order.total_price = total_price
                order.save()
        except:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res':7,'errmsg':'提交订单失败'})

        #todo:事务提交
        transaction.savepoint_commit(save_id)
        # todo:删除用户购物车中的相应记录
        conn.hdel(cart_key, *skulist)

        return JsonResponse({'res': 5, 'errmsg': '订单创建成功'})

#前段ajax post访问/order/pay
#传递的参数:订单id(order_id)
class 订单支付(View):
    def post(self,request):
        #接收参数
        user=request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0,'errmsg':'用户为登陆'})
        #校验参数
        order_id=request.POST.get('order_id')
        print(order_id)
        if not order_id:
            return JsonResponse({'res':1,'errmsg':'订单id为空'})

        try:
            order=OrderInfo.objects.get(order_id=order_id,
                              user=user,
                              pay_method=3,
                              order_status=1)
            print(order)
        except OrderInfo.DoesNotExist:
            #订单不存在
            return JsonResponse({'res':2,'errmsg':'订单id出错'})
        #业务处理:调用支付宝的支付接口
        # from alipay import
        #初始化
        alipay=AliPay(
            appid='2016082600312796',
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR,'apps/order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR,'apps/order/alipay_public_key.pem'),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type = "RSA2",  # RSA 或者 RSA2
            debug = True  # 默认False沙箱选True
        )
        print(alipay)
        #调用支付宝下单接口
        # 电脑网站支付，需要跳转到https://openapi.alipay(沙箱)dev.com/gateway.do? + order_string
        total_pay=order.total_price+order.transit_price#Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(total_pay),
            subject='天天生鲜%s'%order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )
        print(order_string)
        #返回应答
        pay_url='https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res':3,'pay_url':pay_url})


#前段ajax post访问/order/check
#传递参数
class 查询订单支付结果(View):
    def post(self,request):
        # 接收参数
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户为登陆'})
        # 校验参数
        order_id = request.POST.get('order_id')
        print(order_id)
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '订单id为空'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
            print(order)
        except OrderInfo.DoesNotExist:
            # 订单不存在
            return JsonResponse({'res': 2, 'errmsg': '订单id出错'})
        # 业务处理:调用支付宝的支付接口
        # from alipay import
        # 初始化
        alipay = AliPay(
            appid='2016082600312796',
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False沙箱选True
        )
        while True:
            #通过sdk调用支付宝交易查询接口alipay
            response=alipay.api_alipay_trade_query(order_id)

            '''{
                "trade_no": "2017032121001004070200176844",#支付宝交易号
                "code": "10000",#接口调用是否成功
                "invoice_amount": "20.00",
                "open_id": "20880072506750308812798160715407",
                "fund_bill_list": [
                    {
                        "amount": "20.00",
                        "fund_channel": "ALIPAYACCOUNT"
                    }
                ],
                "buyer_logon_id": "csq***@sandbox.com",
                "send_pay_date": "2017-03-21 13:29:17",
                "receipt_amount": "20.00",
                "out_trade_no": "out_trade_no15",
                "buyer_pay_amount": "20.00",
                "buyer_user_id": "2088102169481075",
                "msg": "Success",
                "point_amount": "0.00",
                "trade_status": "TRADE_SUCCESS",#支付状态
                "total_amount": "20.00"
            }'''

            code=response.get('code')

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                #支付成功
                #进行处理:填写支付宝交易号，更新订单状态
                trade_no=response.get('trade_no')
                order.trade_no=trade_no
                order.order_status=4#
                order.save()
                #返回应答
                return JsonResponse({'res':3,'message':'支付成功'})

            elif code=='40004' or code=='10000' and response.get('trade_status') == 'WAIT_BUYER_PAY':
                #等待买家付款
                import time
                time.sleep(5)
                continue
            else:
                #支付出错
                return JsonResponse({'res':4,'errmsg':'支付出错'})

class 订单创建2(View):
    @transaction.atomic#事务开始mysql中的begin
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
        print(addr_id)
        print(type(addr_id))
        print(pay_method)
        print(sku_ids)
        # 数据校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法支付方式'})

        # 校验地址
        try:
            addr = Address.object.get(id=addr_id)
        except:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址信息错误'})

        # 业务处理
        # 组织订单数据
        #todo: 订单id:格式:20171122122930+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 10

        # 总金额和总数目
        total_count = 0
        total_price = 0
        #todo:设置保存点
        save_id=transaction.savepoint()
        try:
            #todo: 向订单信息表中添加已条记录
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             total_price=total_price,
                                             total_count=total_count,
                                             pay_method=pay_method,
                                             transit_price=transit_price
                                             )

            # todo:向订单商品表中添加信息时,用户买了几件商品,需要添加几条记录
            skulist = sku_ids.split(',')
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            print(cart_key)
            for sku_id in skulist:
                try:
                    # todo:悲观锁select_for_update()
                    sku = GoodSKU.objects.select_for_update().get(id=sku_id)
                    # sku = GoodSKU.objects.get(id=sku_id)
                except GoodSKU.DoesNotExist:
                    #商品不存在
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
                # 从redis中获取用户需要购买的商品信息
                count = conn.hget(cart_key, sku_id)

                #判断商品的库存
                if int(count)>sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res':6,'errmsg':'商品库存不足'})

                # todo:向订单表中添加已条记录
                OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    count=count,
                    price=sku.price
                )

                # 更新对应商品的库存和销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()
                # 累加订单中商品总数目和总金额
                total_count += int(count)
                amount = sku.price * int(count)
                total_price += amount
            #todo: 更新订单信息表对应的总件数和总金额
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res':7,'errmsg':'提交订单失败'})

        #todo:事务提交
        transaction.savepoint_commit(save_id)
        # todo:删除用户购物车中的相应记录
        conn.hdel(cart_key, *skulist)

        return JsonResponse({'res': 5, 'errmsg': '订单创建成功'})
