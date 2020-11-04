from django.shortcuts import render

# Create your views here.
# 判断用户名是否重复
from .models import User,AbstractUser
from django.views import View
from django.http import JsonResponse
import json,re
from django_redis import get_redis_connection
from django.contrib.auth import login,authenticate,logout
from ihome.utils.views import LoginRequiredJsonMixin
from django.conf import settings


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
                'errno': 4101,
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

    def get(self,request):
        # 提取参数
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'errno':4101, 'errmsg':'未登录'})
        data = {"name":user.username,"user_id":user.id}
        return JsonResponse({'errno':0,'errmsg':'已登录','data':data})


    # 退出登陆
    def delete(self, request):
        """
        退出登陆，删除用户登陆信息
        """
        # 1、确定用户身份(当前以登陆的用户)
        # request.user ---> 已登陆的用户模型类对象(User) 或 匿名用户对象(AnonymousUser)
        # 2、删除该用户的session登陆数据，清除该用户的登陆状态
        logout(request) # 通过request对象获取用户信息，然后在去清除session数据

        response = JsonResponse({'errno': '0', 'errmsg': '已登出'})
        response.delete_cookie('username')
        return response



#用户个人中心
class UserInfo(LoginRequiredJsonMixin,View):
    def get(self, request):
        #　1.提取参数
        user= request.user
        username=user.username
        image_name = User.objects.get(username=username).avatar.name
        # 2.校验参数
        #  用户未上传头像显示默认头像
        if not image_name:
            image_name = None

        # 3. 业务处理
        # 4. 退回响应
        year = user.date_joined.year
        month = user.date_joined.month
        day = user.date_joined.day
        hour = user.date_joined.hour
        minute = user.date_joined.minute
        second = user.date_joined.second

        return JsonResponse({
            'data':{
                "avatar":image_name,
                "create_time": "%d-%d-%d %02d:%02d:%02d" % (year, month, day, hour, minute, second),
                "mobile": user.mobile,
                "name": user.username,
                "user_id": user.id,
            },
            "errmsg": "OK",
            "errno": "0"
        })


# 用户名修改
class UesrnameUpdataView(LoginRequiredJsonMixin, View):
    def put(self, request):
        # 1.提取参数
        user = request.user
        data = json.loads(request.body.decode())
        new_username = data.get('name')

        # 2.校验参数
        if not new_username:
            return JsonResponse({'errno': 4041, 'errmsg': '缺少必传参数'})

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', new_username):
            return JsonResponse({'errno': 4041, 'errmsg': '用户名格式有误'})

        # 3.业务数据处理：修改用户名
        try:
            user.username = new_username
            user.save()
        except Exception as e:
            return JsonResponse({'errno': 4041, 'errmsg': '用户名修改错误'})

        # 清理状态保持信息
        logout(request)

        response = JsonResponse({'errno': '0', 'errmsg': '修改成功'})
        response.delete_cookie('username')
        return response


# 用户实名认证
class UesrAuthentificationView(LoginRequiredJsonMixin, View):
    def post(self, request):
        # 1.提取参数
        user = request.user
        data = json.loads(request.body.decode())
        real_name = data.get('real_name')
        id_card = data.get('id_card')

        # 2.校验参数
        if not all([real_name, id_card]):
            return JsonResponse({'errno': 4041, 'errmsg': '缺少必传参数'})

        if not re.match(r'^\w{2,20}$', real_name):
            return JsonResponse({'errno': 4041, 'errmsg': '真实名字格式错误'})

        if not re.match(
                r'(^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$)|(^[1-9]\d{5}\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{2}[0-9Xx]$)',
                id_card):
            return JsonResponse({'errno': 4041, 'errmsg': '身份证格式错误'})

        # 3.业务数据处理,添加真实名字和身份证号
        try:
            user.real_name = real_name
            user.id_card = id_card
            user.save()
        except Exception as e:
            return JsonResponse({'errno': 0, 'errmsg': '实名认证失败'})

        return JsonResponse({'errno': '0', 'errmsg': '认证信息保存成功'})