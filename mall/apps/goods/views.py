from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from reversion.compat import is_authenticated

from goods.models import SKU
from goods.serializers import HostSKUListSerializer,UserOrdersSerializer
from orders.models import OrderInfo, OrderGoods

"""
页面静态化  -- 提升用户体验,SEO
其实就是我们现把数据查询出来,查询出来之后,将数据填充到模板中
将html写入到指定的文件,当用户访问的时候,直接访问静态html
"""
"""
列表数据
热销数据
分类数据

热销数据:应该是到哪个分类去获取哪个分类的热销数据

1.获取分类ID
2.根据ID获取数据  [sku,sku]
3.将数据转换为字典或者json数据
4.返回响应

GET   /goods/categories/(?P<category_id>\d+)/hotskus/
"""
from rest_framework.generics import ListAPIView


class HostSKUListAPIView(ListAPIView):

    pagination_class = None

    serializer_class = HostSKUListSerializer

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id).order_by('-sales')[:2]

'''
列表数据的获取
当用户选择一个分类的时候,我们需要对分类数据进行排序,进行分页处理
简化需求,一步一步的实现
现获取所有分类数据,再排序,再分页

现获取所有分类数据
1.先获取所有数据
2.将对象列表转换为字典
3.返回响应

GET    /goods/categories/(?P<category_id>\d+)/skus/
'''
from rest_framework.filters import OrderingFilter


class SKUListAPIView(ListAPIView):
    # 排序
    filter_backends = [OrderingFilter]
    ordering_fields = ['create_time', 'sales', 'price']
    serializer_class = HostSKUListSerializer

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category=category_id)

from .serializers import SKUIndexSerializer
from drf_haystack.viewsets import HaystackViewSet


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    serializer_class = SKUIndexSerializer




"""
订单列表展示

必须是登陆用户才可以访问

# 1. 我们获取用户信息
# 2. 从redis中获取数据
#     hash
#     set
# 3. 需要获取的是 选中的数据
# 4. [sku_id,sku_id]
# 5. [SKU,SKU,SKU]
# 6. 返回相应

GET     /orders/placeorders/


"""

"""
订单列表

获取用户信息
查询数据
校验数据
返回数据
"""
# class SKUOrderView(ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = OrderCenterSerializer
#     # queryset = OrderInfo.objects.all()
#
#     def get_queryset(self):
#         user = self.request.user
#
#         queryset = user.orderinfo_set.all()
#         return queryset

class SKUOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        user = request.user
        orders = user.orderinfo_set.all()

        serializer = UserOrdersSerializer(orders,many=True)
        return Response(serializer.data)
    # def get(self, request, *args, **kwargs):
    #     """
    #     # 6. 返回相应
    #     # serializer = OrderSKUSerialzier(skus,many=True)
    #     # data = {
    #     #     'freight':10,
    #     #     'skus':serializer.data
    #     # }
    #     #
    #     # return Response(data)
    #     # return Response(serializer.data)
    #
    #     """
    #     # serializer = OrderGoodsSerialzier(many=True)
    #     # data ={
    #     #     '',
    #     #     'goods':serializer.data
    #     # }
    #     # return Response(data)
    #
    #     user = request.user
    #     try:
    #         orders = OrderInfo.objects.filter(user_id=user.id)
    #     except Exception as e:
    #         return Response('没有orders')
    #
    #     order_goods = OrderGoods.objects.filter(order_id=orders.order_id)
    #     goods_dic = {}
    #     # for goods in order_goods:
    #     #
    #     #
    #     # data = {
    #     #
    #     # }



