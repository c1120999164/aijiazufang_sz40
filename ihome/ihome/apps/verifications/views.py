from django.shortcuts import render
from django.views import View
from django.http import JsonResponse, HttpResponse
# get_redis_connection("verify_code")
# 功能：获取一个redis的连接对象
# 参数：django缓存配置选项
# 返回值：连接对象
from django_redis import get_redis_connection
from celery_tasks.sms.tasks import ccp_send_sms_code
from .libs.captcha.captcha import captcha
# from verifications.libs.yuntongxun.ccp_sms import CCP
import re, random,json
# 发送短信验证码接口

class ImageCodeView(View):
    def get(self, request):
        # 1.提取参数
        # data = json.loads(request.body.decode())
        cur = request.GET.get('cur')
        pre = request.GET.get('pre')
        # 2.校验参数
        # 2.1必要性校验
        if not cur:
            return JsonResponse({'errno': 4103, 'errmsg': '参数错误'})

        # 3.业务数据处理-生成图片验证码。存入redis２号库
        # 3.1 生成图片验证码
        text, image = captcha.generate_captcha()
        # print(text, image)
        # 3.2验证码text存入redis(以 cur作为key）
        # set img_<cur> <text>
        # 获取缓存项“verify_code‘
        try:
            conn = get_redis_connection('verify_code')
            # 存入图片验证码，设置有效期为３００秒
            conn.setex('img_%s' % cur, 300, text)

        except Exception as e:
            return JsonResponse({
                'errno': 4001, 'errmsg': '保存图形验证码错误'
            })

        # 4.构建响应
        return HttpResponse(image, content_type='image/jpeg')


class SMSCodeView(View):

    def post(self, request):
        # 提取参数
        # image_code = request.GET.get('image_code')  # 用户填写的图片验证码
        # uuid = request.GET.get('image_code_id')  # 用户图形验证码的uuid
        # mobile =
        data = json.loads(request.body.decode())
        mobile = data.get('mobile')
        text = data.get('text')# 用户输入的图形验证码
        id = data.get('id')
        # 校验参数
        if not all([mobile,id,text]):
            return JsonResponse({'code': 4101, 'errmsg': '缺少必要参数'})
        # if not re.match(r'^[a-zA-Z0-9]{4}$', image_code):
        #     return JsonResponse({'code': 4101, 'errmsg': '图形验证码格式有误'})
        # if not re.match(r'^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$', uuid):
        #     return JsonResponse({'code': 4101, 'errmsg': 'uuid格式有误'})

        # 图形验证码校验 —— 根据uuid获取redis中的图形验证码，和用户填写的比对
        conn = get_redis_connection('verify_code')  # 2号
        text1 = conn.get('img_%s' % id)  # b"TYUP", redis客户端读取返回的数据统一是"字节"类型
        # 为了保证图片验证码之后被使用一次，只需要读一次立刻删除
        conn.delete('img_%s' % id)
        if not text1:
            # 如果图形验证码过期，text返回为空
            return JsonResponse({'errno': 4101, 'errmsg': '图形验证码过期'})
        #  b"YUPO".decode() --> "YUPO"
        if text.lower() != text1.decode().lower():  # 统一转化小写对比，意味着忽略大小写
            return JsonResponse({'errno': 4101, 'errmsg': '图形验证码错误！'})

        # 业务数据处理 —— 发送短信
        # 用户每次发送短信时,给该手机号标记一段唯一码,持续60s
        # 当用户再次发送短信时,判断是否有该唯一编码
        flag = conn.get('send_flag_%s' % mobile)
        if flag:
            # 若有唯一编码,证明该手机号60s内发送过短信,直接返回
            return JsonResponse({'errno': 4101, 'errmsg': '请勿频繁发送短信'})
        # 生成固定6位数长度的0-9字符组成的验证码
        sms_code = "%06d" % random.randrange(0, 999999)
        print('短信：', sms_code)

        # 把短信验证码写入redis
        conn.setex('sms_%s'%mobile, 300, sms_code)

        # 用户成功发送短信,给该手机号写入一段唯一编码
        conn.setex('send_flag_%s'%mobile,60,1)

        # 使用redis的pipline功能,把多个redis指令打包执行
        # 1.获取redis的pipeline对象
        p = conn.pipeline()
        # 2.使用pipeline的对象方法实现调用指令
        p.setex('sms_%s' % mobile, 300, sms_code)  # 此处调用对象方法不会通信,只是把需求放入队列中
        # 3.提交pipeline把指令通过网络一次性提交
        p.execute()
        # 发送短信
        ccp_send_sms_code.delay(mobile,sms_code)

        # 4、构建响应
        return JsonResponse({'errno': 0, 'errmsg': 'ok'})
