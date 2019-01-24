from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.utils.deconstruct import deconstructible
from mall import settings
# 1.您的自定义存储系统必须是以下子类 django.core.files.storage.Storage：

# 4.您的存储类必须是可解构的， 以便在迁移中的字段上使用它时可以对其进行序列化。
# 只要您的字段具有可自行序列化的参数，
# 就 可以使用 django.utils.deconstruct.deconstructible类装饰器


@deconstructible
class MyStorage(Storage):
    # 2.Django必须能够在没有任何参数的情况下实例化您的存储系统。
    #  这意味着任何设置都应该来自django.conf.settings：
    def __init__(self, config_path=None, config_url=None):
        if not config_path:
            fdfs_path = settings.FDFS_CLIENT_CONF
            self.fdfs_path = fdfs_path
        if not config_url:
            fdfs_url = settings.FDFS_URL
            self.fdfs_url = fdfs_url

    # 3.您的存储类必须实现_open()和_save()
    # 方法以及适用于您的存储类的任何其他方法。
    def open(self, name, mode='rb'):
        pass

    def save(self, name, content, max_length=None):
        # name,           文件的名字,我们不能通过名字获取文件的完整路径
        # content,        内容,就是上传的内容,二进制
        # max_length=None
        # 1.创建fdfs的客户端,额昂客户端加载配置
        # client = Fdfs_client('utils/fastdfs/client.conf')
        # client = Fdfs_client(settings.FDFS_CLIENT_CONF)
        client = Fdfs_client(self.fdfs_path)
        # 2.获取上传的文件
        # content.read()就是读取content的内容,读取的是二进制
        file_data = content.read()
        # 3.上传图片并获取返回内容
        # upload_by_buffer 上传二进制流
        result = client.upload_by_buffer(file_data)
        # 4.根据返回内容,获取remote file_id
        if result.get('Status') == 'Upload successed.':
            # 说明上传成功
            fild_id = result.get('Remote file_id')
        else:
            raise Exception('上传失败')
        # 需要把fild_id返回回去
        return fild_id

    # exists 存在
    # fdfs做了重名的处理,我们只需要上传就可以了
    def exists(self, name):
        return False

    def url(self, name):

        # return 'http://192.168.186.128:8888/' + name
        # return settings.FDFS_URL + name
        return self.fdfs_url + name

