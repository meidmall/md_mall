from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^imagecodes/(?P<image_code_id>.+)/$', views.RegisterImageCodeView.as_view()),
    url(r'^smscodes/(?P<mobile>1[345789]\d{9})/$', views.RegisterSmscodeView.as_view(),)
]