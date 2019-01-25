from decimal import Decimal
from django.shortcuts import render

# Create your views here.
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection

from goods.models import SKU
from orders.models import OrderGoods
from orders.serializers import OrderSKUAPIView, OrderPlaceSerializer, OrderSerializer, CommentShowSerializer

'''
订单列表展示
必须是登陆用户才可以访问

1.我们获取用户信息
2.从redis中获取数据
3.需要获取的是选中的数据
4.[sku_id,sku_id]
5.[sku,sku,sku]
6.返回响应
'''


class PlaceOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1.我们获取用户信息
        user = request.user
        # 2.从redis中获取数据
        redis_conn = get_redis_connection('cart')
        # 3.需要获取的是选中的数据
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
        cart = {}
        # 4.[sku_id,sku_id]
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(redis_cart[sku_id])
        # 5.[sku,sku,sku]
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]
        # 6.返回响应
        # serializer = OrderSKUAPIView(skus, many=True)
        freight = Decimal('10.00')
        serializer = OrderPlaceSerializer({
            'freight': freight,
            'skus': skus
        })
        return Response(serializer.data)

'''
提交订单
1.接收前端数据(用户信息,地址信息,支付方式)
2.验证数据
3.数据入库
4.返回响应

POST
'''


class OrderAPIView(CreateAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

from rest_framework.generics import ListAPIView, RetrieveAPIView


class CommentShowAPIView(ListAPIView):

    serializer_class = CommentShowSerializer

    def get_queryset(self):
        sku_id = self.kwargs['pk']
        return OrderGoods.objects.filter(pk=sku_id)


# class CommentAPIView(APIView):
#
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request, sku_id):
#         data = request.data
#         serializer = CommentSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)



