'''
异步程序的朱脚本模块
'''
from celery import Celery #导入Celery模块

# 1.初始化一个Celery对象－－异步程序对象
celery_app = Celery()
# 2.加载配置文件
celery_app.config_from_object('celery_tasks.config') # 参数是配置文件导包路径,需要先创建一个配置文件
# 3.注册任务
# (1) 发送短信任务,参数传入任务包的导包路径
celery_app.autodiscover_tasks(["celery_tasks.sms"])
