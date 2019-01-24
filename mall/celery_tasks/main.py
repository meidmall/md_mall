from celery import Celery

# 1.celery 是一个即插即用的任务队列
# celery是需要和django(当前的工程)进行交互
# 让celery加载当前工程的默认配置文件

# 第一种方式:
# import os
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mall.settings")

# 第二种方式:
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mall.settings'

# 创建celery实例
# main习惯添加celery的文件路径
# 确保main不会出现重复
app = Celery(main='celery_tasks')

# 3.设置broker
app.config_from_object('celery_tasks.config')

# 4.让celery自动检测任务
app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.mail', 'celery_tasks.html'])

# 5. 让worker去执行任务
# 需要在虚拟环境中执行指令
# celery -A celery实例对象的文件路径 worker -l info
# celery -A celery_tasks.main worker -l info




