from rest_framework import serializers

from goods.models import SKU


class CartSerializer(serializers.Serializer):

    count = serializers.IntegerField(label='个数', required=True)
    sku_id = serializers.IntegerField(label='商品id', required=True)
    selected = serializers.BooleanField(label='勾选状态', default=True, required=False)

    def validate(self, attrs):
        sku_id = attrs.get('sku_id')
        # 商品是否存在
        try:
            sku = SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')
        # 商品的个数是否充足
        if sku.stock < attrs['count']:
            raise serializers.ValidationError('库存不足')
        return attrs


class CartSKUSerializer(serializers.ModelSerializer):

    count = serializers.IntegerField(label='个数', required=True)
    selected = serializers.BooleanField(label='勾选状态', default=True, required=False)

    class Meta:
        model = SKU
        fields = ['id', 'count', 'selected', 'name', 'price', 'default_image_url']


class CartDeleteSerializer(serializers.Serializer):

    sku_id = serializers.IntegerField(label='商品id', required=True)

    def validate(self, attrs):
        try:
            sku = SKU.objects.get(pk=attrs['sku_id'])
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')
        return attrs