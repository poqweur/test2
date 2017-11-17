from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
import os
import time
#加载django文件
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Fresheveryday.settings")
import django
#启动django初始化
django.setup()

#创建celery对象,指定中间人路径
app=Celery('celery_tasks.tasks',broker='redis://127.0.0.1:6379/5')

#创建任务函数
@app.task
def send_register_actie_email(to_email,username,token):
    email_title = '天天生鲜欢迎信息'
    email_body = ''
    send = settings.EMAIL_FROM
    receive=[to_email]
    html='<h1>%s,欢迎你成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://192.168.109.131:8000/user/active/%s">http://192.168.109.131:8000/user/active/%s</a>'%(username,token,to_email)
    time.sleep(5)
    send_mail(email_title, email_body, send, receive,html_message=html)

