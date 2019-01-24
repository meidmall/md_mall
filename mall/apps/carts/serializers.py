from rest_framework import serializers

# serializers.ModelSerializer
# serializers.Serializer
from goods.models import SKU


class CartSerializer(serializers.Serializer):

    # 商品个数
    count = serializers.IntegerField(label='个数',required=True)
    #商品id
    sku_id=serializers.IntegerField(label='sku_id',required=True)
    selected=serializers.BooleanField(label='选中状态',default=True,required=False)



    def validate(self, attrs):

        # 1.商品是否存在,
        sku_id = attrs.get('sku_id')
        try:
            sku = SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')
        #
        # 2.商品的个数是否充足
        if sku.stock < attrs['count']:
            raise serializers.ValidationError('库存不足')

        return attrs


class CartSKUSerializer(serializers.ModelSerializer):

    count = serializers.IntegerField(label='个数',read_only=True)
    selected=serializers.BooleanField(label='选中的状态',read_only=True)

    class Meta:
        model = SKU
        fields =('id','count', 'name', 'default_image_url', 'price', 'selected')



class CartDeleteSerialzier(serializers.Serializer):

    sku_id = serializers.IntegerField(label='商品id',required=True)

    def validate(self, attrs):

        # 1.商品是否存在,
        sku_id = attrs.get('sku_id')
        try:
             SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')


        return attrs
