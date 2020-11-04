
from django.urls import re_path,path
from . import views


urlpatterns = [
    # 路由映射指的就是，把一个请求(HTTP请求)和处理的视图函数(方法)一一对应起来(映射);
    # 路由映射公式：请求方式 + 请求路径 = 视图方法
    # GET + usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/ = UsernameCountView.get()
    # path('usernames/<username:username>/count/', views.UsernameCountView.as_view()),

    path('mobiles/<mobile:mobile>/count/', views.MobileCountView.as_view()),

    re_path(r'^api/v1.0/users$', views.RegisterView.as_view()),

    re_path(r'^api/v1.0/session$', views.LoginView.as_view()),
]