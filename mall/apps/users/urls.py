from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns = [
    # /users/usernames/(?P<username>\w{5,20})/count/
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.RegisterUsernameAPIView.as_view(), name='usernamecount'),
    url(r'^phones/(?P<mobile>1[3-9]\d{9})/count/$', views.RegisterMobileAPIView.as_view()),
    url(r'^$', views.RegisterUserAPIView.as_view()),
    # url(r'^auths/$', obtain_jwt_token),
    url(r'^auths/$', views.MergeLoginAPIView.as_view()),
    # jwt把用户名和密码给系统,让系统进行认证,认证成功之后,jwt生成token
    url(r'^infos/$', views.UserCenterInfoAPIView.as_view()),
    url(r'^emails/$', views.UserEmailInfoAPIView.as_view()),
    url(r'^emails/verification/$', views.UserEmailVerificationAPIView.as_view()),
    url(r'^addresses/$', views.UserAddressAPIView.as_view()),
    url(r'^browerhistories/$', views.UserHistoryAPIView.as_view()),
    # url(r'^address/$', views.UserAddressListAPIView.as_view())
    url(r'^(?P<pk>\d+)/password/$', views.ChangePasswordAPIView.as_view()),
]