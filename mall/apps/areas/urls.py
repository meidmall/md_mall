from django.conf.urls import url
from .views import AreaModelViewSet

urlpatterns = []

# 1. 导入 Router
from rest_framework.routers import DefaultRouter

# 2.创建router实例对象
router = DefaultRouter()

# 3. 注册路由
router.register(r'infos',AreaModelViewSet,base_name='area')

# 4.添加到 urlpatterns

urlpatterns += router.urls