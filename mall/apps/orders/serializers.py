from django_redis import get_redis_connection
from rest_framework import serializers

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from django.db import transaction

from users.models import User


class OrderSKUAPIView(serializers.ModelSerializer):

    count = serializers.IntegerField(label='个数', required=True)

    class Meta:
        model = SKU
        fields = ['id', 'count', 'name', 'price', 'default_image_url']


class OrderPlaceSerializer(serializers.Serializer):

    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = OrderSKUAPIView(many=True)


class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        # 系统默认提供的create方法不能满足我们的需求,我们需要重写
        # 1.生成订单信息
        # 1.1 获取user信息
        user = self.context['request'].user
        # 1.2 获取地址信息
        address = validated_data.get('address')
        # 1.3 获取支付方式
        pay_method = validated_data.get('pay_method')
        # 1.4 判断支付状态
        if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH']:
            status = OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        else:
            status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
        # 1.5 订单id(订单id我们采用自己生成的方式)
        # 时间(年月日时分秒)+6位id信息
        from django.utils import timezone
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%06d' % user.id
        # 1.6 运费,价格和数量 先为 0
        from decimal import Decimal
        freight = Decimal('10.00')
        total_count = 0
        total_amount = Decimal('0')
        # with 语法,对部分代码实现事务功能
        with transaction.atomic():
            # 事务回滚点
            save_point = transaction.savepoint()
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                pay_method=pay_method,
                total_count=total_count,
                total_amount=total_amount,
                freight=freight,
                status=status,
            )
            # 2.生成订单商品(列表)信息
            # 2.1 连接redis
            redis_conn = get_redis_connection('cart')
            # 2.2  hash
            redis_id_count = redis_conn.hgetall('cart_%s' % user.id)
            # set
            redis_selected_ids = redis_conn.smembers('cart_selected_%s' % user.id)
            # 2.3  选中商品的信息  {sku_id:count}
            selected_cart = {}
            for sku_id in redis_selected_ids:
                selected_cart[int(sku_id)] = int(redis_id_count[sku_id])
            # 2.4  [sku_id,sku_id,...]
            ids = selected_cart.keys()
            # 2.5  [SKU,SKU,SKU]
            skus = SKU.objects.filter(pk__in=ids)
            # 2.6 对列表进行遍历
            for sku in skus:
                # SKU
                count = selected_cart[sku.id]
                # 判断库存
                if count > sku.stock:
                    # 出现异常就回滚到指定的保存点
                    transaction.savepoint_rollback(save_point)
                    raise serializers.ValidationError('库存不足')
                # 减少库存
                # sku.stock -= count
                # # 添加销量
                # sku.sales += count
                # sku.save()

                # 用乐观锁来实现并发
                # 1.先记录(查询)库存
                old_stock = sku.stock
                old_sales = sku.sales
                # 2.把更新的数据准备出来
                new_stock = sku.stock - count
                new_sales = sku.sales + count
                # 3.更新数据的时候再查询一次,是否和之前的记录一致
                rect = SKU.objects.filter(pk=sku.id, stock=old_stock).update(stock=new_stock, sales=new_sales)
                if rect == 0:
                    # 说明下单失败
                    transaction.savepoint_rollback(save_point)
                    raise serializers.ValidationError('下单失败')
                # 累加 计算总数量和总价格
                order.total_count += count
                order.total_amount += (count * sku.price)
                # 生成OrderGoods信息
                OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    count=count,
                    price=sku.price
                )
            # 保存订单修改的信息
            order.save()
            # 如果全部没有问题,提交事务
            transaction.savepoint_commit(save_point)
            # 生成订单之后一定要删除购物出的内容
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *redis_id_count)
            pl.srem('cart_selected_%s' % user.id, *redis_selected_ids)
            pl.execute()

        return order


class CommentShowSerializer(serializers.ModelSerializer):

    username = serializers.CharField(label='username')

    class Meta:
        model = OrderGoods
        fields = ['comment', 'is_anonymous', 'score', 'username']


class CommentUserSerializer(serializers.ModelSerializer):

    comment = CommentShowSerializer(many=True)

    class Meta:
        model = OrderInfo
        fields = ['user', 'comment']


class SkuSerializer(serializers.ModelSerializer):

    class Meta:
        model = SKU
        fields = ('name', 'default_image_url','id')


class ScoreOrderSerializer(serializers.ModelSerializer):
    sku = SkuSerializer()

    class Meta:
        model = OrderGoods
        fields = ('sku','comment','price','is_anonymous')


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderGoods
        fields = ['order', 'sku', 'comment', 'score', 'is_anonymous']

    # def create(self, validated_data):
    #
    #     # user = self.context['request'].user
    #     order = validated_data['order']
    #     sku = validated_data['sku']
    #     comment = validated_data['comment']
    #     score = validated_data['score']
    #     is_anonymous = validated_data['is_anonymous']
    #
    #     instance = OrderGoods.objects.filter(order_id=order.order_id).update(
    #         order_id=order.order_id,
    #         sku_id=sku,
    #         comment=comment,
    #         score=score,
    #         is_anonymous=is_anonymous,
    #     )
    #
    #     return instance