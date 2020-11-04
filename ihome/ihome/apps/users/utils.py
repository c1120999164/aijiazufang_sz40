# 自定义认证后端,实现多账号登录
# 导入用户模型类,从数据库查询信息
from .models import User
# 导入系统配置文件
from django.conf import settings
# 导入django自带的认证后端模块
from django.contrib.auth.backends import ModelBackend
# 定义自己的认真后端并继承django自带的认证后端
# 导入django中的用户模型类的Q方法,实现or逻辑,手机号或用户名任意匹配一个皆可
from django.db.models import Q
# from ihome.utils.secret import SecretOauth
class UsernameMobileAuthBackend(ModelBackend):
    # 重写其中的判断方法,加入手机号判断
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 如果手机号和用户名都匹配失败的话,会抛出异常,先捕获异常
        try:
            # 获取模型类对象,用前端返回的username与数据库中的用户名和手机号比较
            # 满足其中一个就行
            user = User.objects.get(Q(username=username)|Q(mobile=username))
        #
        except Exception:
            return None
        # 通过用户名或手机号找到用户之后,开始检查密码
        # 用模型类中的check_password方法,
        if user.check_password(password):
            return user

