from celery import Celery

"""
1. 创建任务
2. 创建Celery实例
3. 在celery中 设置 任务,broker
4. worker


"""


#1. celery 是一个 即插即用的任务队列
# celery 是需要和 django(当前的工程) 进行交互的
# 让celery加载当前的工程的默认配置

#第一种方式:
# import os
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mall.settings")

#第二种方式:
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mall.settings'


#2.创建celery实例
# main 习惯 添加 celery的文件路径
# 确保 main 不出现重复
app = Celery(main='clery_tasks')

#3. 设置broker
# 加载 broker的配置信息:  参数: 路径信息
app.config_from_object('clery_tasks.config')

#4. 让celery自动检测任务
#  参数: 列表
# 元素: 任务的包路径
app.autodiscover_tasks(['clery_tasks.sms','clery_tasks.mail','clery_tasks.html'])



#5. 让worker 去执行任务
# 需要在虚拟环境中 执行指令
# celery -A celery实例对象的文件路径 worker -l info
#celery -A clery_tasks.main worker -l info




