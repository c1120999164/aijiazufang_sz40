"""
自定义登陆验证视图拓展类
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

class LoginRequiredJsonMixin(LoginRequiredMixin):

    def handle_no_permission(self):
        # 基于前后端分离，需要返回一个JsonResponse
        return JsonResponse({'code': 400, 'errmsg': '未登陆！'})
