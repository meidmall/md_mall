from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView

from areas.models import Area
from areas.serailizers import AreaSerializer, SubsAreaSerialzier

"""
id      name        parent_id

1000    北京省         null

1010    北京市         1000

1011    昌平区         1010
1012    海淀区         1010
1013    朝阳区         1010

"""


"""
1. 获取省份信息的时候
select * from tb_areas where parent_id is null;


2. 获取市的信息的时候
3. 获取区县的信息的时候
select * from tb_areas where parent_id=110000;
select * from tb_areas where parent_id=110100;

"""
# class AreaProviceAPIView(APIView):
#     #获取省份信息
#     def get(self,request):
#         #
#         pass
#
#
# class AreaDistrictAPIView(APIView):
#     # 获取市,区县信息
#     def get(self, request):
#         pass

    # http://127.0.0.1:8000/areas/infos/        省份信息            list 方法

# http://127.0.0.1:8000/areas/infos/110000  市区县信息           retrieve


from rest_framework.viewsets import ReadOnlyModelViewSet

from rest_framework_extensions.cache.mixins import ListCacheResponseMixin
from rest_framework_extensions.cache.mixins import RetrieveCacheResponseMixin
from rest_framework_extensions.cache.mixins import CacheResponseMixin
class AreaModelViewSet(CacheResponseMixin,ReadOnlyModelViewSet):

    #让它不是使用分类类
    pagination_class = None

    # queryset = Area.objects.all()   #所有信息
    # queryset = Area.objects.filter(parent=None)   #省的信息

    def get_queryset(self):

        # 我们可以根据 不同的业务逻辑返回不同的数据源
        if self.action == 'list':
            # Area.objects.filter(parent__isnull=True)
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    # serializer_class = AreaSerializer

    def get_serializer_class(self):

        # 我们可以根据 不同的业务逻辑返回不同的 序列化器
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubsAreaSerialzier

