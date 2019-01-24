

# 任务 就是普通的函数
# 1. 这个普通的函数  必须要被 celery实例对象的 task装饰器装饰
#2. 这个任务 需要 celery 自己去 检测
from libs.yuntongxun.sms import CCP
from clery_tasks.main import app

@app.task
def send_sms_code(mobile,sms_code):

    CCP().send_template_sms(mobile, [sms_code, 5], 1)