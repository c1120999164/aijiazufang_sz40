from django.shortcuts import render

# Create your views here.
# 判断用户名是否重复
from .models import User,AbstractUser
from django.views import View
from django.http import JsonResponse
import json,re
from django_redis import get_redis_connection
from django.contrib.auth import login,authenticate,logout


# 判断手机号是否重复
class MobileCountView(View):

    def get(self, request, mobile):
        # 1、提取参数
        # 2、校验参数
        # 3、业务数据处理
        count = User.objects.filter(
            mobile=mobile
        ).count()
        # 4、构建响应
        return JsonResponse({
            'errno': 0,
            'errmsg': 'ok',
            'count': count
        })


# 用户注册
class RegisterView(View):

    def post(self, request):
        # 提取参数
        data = json.loads(request.body.decode())
        # data = json.loads(request.body)

        password = data.get('password')
        # password2 = data.get('password2')
        mobile = data.get('mobile')
        phonecode = data.get('phonecode')


        # 校验参数
        # 必要性校验
        if not all([password, mobile, phonecode]):
            return JsonResponse({
                'errno': 4101,
                'errmsg': '缺少必要参数',
            }, status=400)
        # 约束条件校验

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({
                'errno': 4101,
                'errmsg': '密码格式有误',
            }, status=400)
        # 2次输入密码是否一致
        # if password != password2:
        #     return JsonResponse({
        #         'code': 4101,
        #         'errmsg': '两次输入密码不一致',
        #     }, status=400)

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({
                'errno': 4101,
                'errmsg': '手机号格式有误',
            }, status=400)

        if not re.match(r'^\d{6}$', phonecode):
            return JsonResponse({
                'code': 4101,
                'errmsg': '短信验证码格式有误',
            }, status=400)

        # 业务性校验(短信验证校验)
        # 此处填充短信验证码校验逻辑代码
        conn = get_redis_connection('verify_code') # 2号
        sms_code_from_redis = conn.get('sms_%s'%mobile)
        if not sms_code_from_redis:
            return JsonResponse({'errno': 4101, 'errmsg': '短信验证码过期'})

        if phonecode != sms_code_from_redis.decode():
            return JsonResponse({'errno': 4101, 'errmsg': '短信验证码有误'})

        # 业务数据处理 —— 新建User模型类对象保存数据库
        try:
            user = User.objects.create_user(
                username=mobile,
                password=password,
                mobile=mobile
            )

        except Exception as e:
            print(e)
            return JsonResponse({
                'errno': 4101,
                'errmsg': '数据库写入失败'
            }, status=500)

        # TODO: 状态保持 —— 使用session机制，把用户数据写入redis
        login(request, user)

        # 构建响应
        response = JsonResponse({'errno': 0, 'errmsg': 'ok'})
        # TODO 设置cookie,记录用户名
        response.set_cookie('username', mobile, max_age=3600 * 24 * 14)
        return response





# 传统用户名密码登录
class LoginView(View):
    def post(self,request):
        # 从请求体中提取参数
        data = json.loads(request.body.decode())
        username = data.get('mobile')
        password = data.get('password')
        # 调用django自带的authenticate参数进行用户名密码验证
        user = authenticate(request, username=username, password=password)
        if not user:
            # 如果验证失败,返回响应
            return JsonResponse({'errno':4101,'errmsg':'用户名或密码错误'})
        # TODO:状态保持
        login(request,user)

        # 判断是否记住用户,若用户勾选记住密码,remembered返回值为True
        response = JsonResponse({'errno':0,'errmsg':'ok'})
        # TODO 设置cookie,记录用户名
        response.set_cookie('username',username,max_age=3600*24*14)
        # merge_cart_cookie_to_redis(request=request, response=response)
        return response