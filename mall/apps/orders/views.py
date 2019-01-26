from decimal import Decimal
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection

from goods.models import SKU
from orders.models import OrderGoods, OrderInfo
from orders.serializers import OrderSKUAPIView, OrderPlaceSerializer, OrderSerializer, \
    CommentSerializer, ScoreOrderSerializer, CommentShowSerializer, CommentUserSerializer

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

from rest_framework.generics import ListAPIView


class CommentShowAPIView(ListAPIView):

    serializer_class = CommentShowSerializer

    # def get_queryset(self):
    #     sku_id = self.kwargs['sku_id']
    #     return OrderGoods.objects.filter(sku_id=sku_id, is_commented=True)

    def get(self, request, *args, **kwargs):
        sku_id = self.kwargs['sku_id']
        goods = OrderGoods.objects.filter(sku_id=sku_id, is_commented=True)
        order_goods = []
        for good in goods:
            order_id = good.order.order_id
            order_info = OrderInfo.objects.get(order_id=order_id)
            user = order_info.user
            username = user.username
            comment = good.comment
            score = good.score
            is_anonymous = good.is_anonymous
            data = {
                'username': username,
                'comment': comment,
                'score': score,
                'is_anonymous': is_anonymous
            }
            order_goods.append(data)
        return Response(order_goods)
        # serializer = CommentShowSerializer(data=order_goods, many=True)
        # serializer.is_valid(raise_exception=True)
        # return Response(serializer.data)



# class CommentShowAPIView(APIView):
#
#     def get(self, request, sku_id):
#         comment_set = OrderGoods.objects.filter(sku=sku_id, is_commented=True)
#         data=[]
#         for comment in comment_set:
#             innner_data = {
#                 "username": comment.order.user.username,
#                 "comment": comment.comment,
#                 "score": comment.score,
#                 "is_anonymous": comment.is_anonymous
#             }
#             data.append(innner_data)
#         serializer = CommentShowSerializer(data=data, many=True)
#         serializer.is_valid(raise_exception=True)
#         return Response(serializer.data)


class ScoreOrderView(APIView):

    def get(self,request,order_id):
        skus = OrderGoods.objects.filter(order_id__exact=order_id)
        serializers = ScoreOrderSerializer(skus, many=True)
        return Response(serializers.data)


class CommentAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        data = request.data
        serializer = CommentSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        order = serializer.validated_data.get('order')
        sku = serializer.validated_data.get('sku')
        comment = serializer.validated_data.get('comment')
        score = serializer.validated_data.get('score')
        is_anonymous = serializer.validated_data.get('is_anonymous')

        # 3. 数据入库
        try:
            comment_good = OrderGoods.objects.get(order=order, sku=sku)
        except OrderGoods.DoesNotExist:
            return Response({'message': '产品信息有误'}, status=status.HTTP_400_BAD_REQUEST)

        comment_good.comment = comment
        comment_good.score = score
        comment_good.is_anonymous = is_anonymous
        comment_good.is_commented = True

        comment_good.save()

        # 4. 返回相应
        return Response({
            'comment': comment,
            'score': score,
            'is_anonymous': is_anonymous,
        })


# class CommentAPIView(CreateAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = CommentSerializer
#
#     def get_queryset(self):
#         order_id = self.kwargs.get('order')
#         return OrderGoods.objects.filter(pk=order_id)
