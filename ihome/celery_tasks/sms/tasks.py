# 该文件名固定,只能为tasks,是用于定义任务的地方
from celery_tasks.main import celery_app

from celery_tasks.yuntongxun.ccp_sms import CCP
# 定义一个发送短信的任务
@celery_app.task(name = "ccp_send_sms_code")
def ccp_send_sms_code(moble,sme_code):
    # 功能:发送短信
    # 参数:手机号,验证码信息
    ccp = CCP()
    ret = ccp.send_template_sms(
        moble,[sme_code,5],1
    )
    # 返回值:发送成功与否
    return ret




