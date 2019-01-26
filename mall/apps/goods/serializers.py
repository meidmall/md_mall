from rest_framework import serializers

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods


class HostSKUListSerializer(serializers.ModelSerializer):

    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')


from .search_indexes import SKUIndex
from drf_haystack.serializers import HaystackSerializer

class SKUIndexSerializer(HaystackSerializer):
    """
    SKU索引结果数据序列化器
    """
    class Meta:
        index_classes = [SKUIndex]
        fields = ('text', 'id', 'name', 'price', 'default_image_url', 'comments')


# class OrderSKUAPIViewV(serializers.ModelSerializer):
#
#     class Meta:
#         model = OrderGoods
#         fields = ['name', 'price', 'default_image_url']
#
# class OrderCenterSerializer(serializers.ModelSerializer):
#
#
#     class Meta:
#         model = OrderInfo
#         fields = ['create_time','order_id','pay_method','status','total_amount','freight','total_count']
#
class UserSkuOrderGoodsSerializer(serializers.ModelSerializer):

    class Meta:
        model = SKU
        fields = ['name','default_image_url']


class UserOrderGoodsSerializer(serializers.ModelSerializer):

    sku = UserSkuOrderGoodsSerializer()
    # orders = UserOrdersSerializer(many=True)
    # price = serializers.DecimalField(max_digits=10, decimal_places=2, verbose_name="单价")
    # count = serializers.IntegerField(default=1, verbose_name="数量")

    class Meta:
        model = OrderGoods
        fields = ['id', 'count', 'price', 'order_id', 'sku_id','sku']

class UserOrdersSerializer(serializers.ModelSerializer):

    skus = UserOrderGoodsSerializer(many=True)
    # create_time = serializers.DateTimeField(decimal_places=0)
    class Meta:
        model = OrderInfo
        fields = ['create_time','order_id', 'total_amount', 'pay_method', 'status', 'skus','freight']

