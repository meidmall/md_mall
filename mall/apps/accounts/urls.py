from django.conf.urls import url

from accounts import views

urlpatterns = [
    url(r'(?P<username>\w{5,20})/sms/token/$',views.ForGetPasswordAPIView.as_view()),
    url(r'code/$',views.SmscodeAPIView.as_view()),
    # url(r'',views.AuthenticationAPIView.as_view())
    url(r'(?P<username>\w{5,20})/password/token/$',views.SmscodeVerification.as_view())

]