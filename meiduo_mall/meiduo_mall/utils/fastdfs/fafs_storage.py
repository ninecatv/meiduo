from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FastDFSStorage(Storage):
    """自定义文件存储系统类"""
    def __init__(self, client_conf=None, base_url=None):
        """
        初始化方法
        :param client_conf: fastdfs客户端配置文件地址
        :param base_url: storage  ip:端口
        """
        # if client_conf:
        #     self.client_conf = client_conf
        # else:
        #     self.client_conf = settings.FDFS_CLIENT_CONF
        # if base_url:
        #     self.base_url = base_url
        # else:
        #     self.base_url = settings.FDFS_BASE_URL

        # self.client_conf = client_conf if client_conf else settings.FDFS_CLIENT_CONF
        # self.base_url = base_url if base_url else settings.FDFS_BASE_URL

        self.client_conf = client_conf or settings.FDFS_CLIENT_CONF
        self.base_url = base_url or settings.FDFS_BASE_URL

    def _open(self, name, mode='rb'):
        """此方法是打开文件, 自定义文件存储系统只为实现上传和下载, 所以此方法什么也不做直接pass"""
        pass

    def _save(self, name, content):
        """
        上传图片时会调用此方法
        :param name: 上传的文件名
        :param content: 上传文的文件对象, 可以通过content.read()方法获取文件的二进制数据
        :return: 返回file_id 将来会保存在数据库image字段
        """
        # 创建fdfs客户端
        # client = Fdfs_client('meiduo_mall/utils/fastdfs/client.conf')
        # client = Fdfs_client(settings.FDFS_CLIENT_CONF)
        client = Fdfs_client(self.client_conf)

        # client.upload_by_filename(client)  # 如果指定一个文件路径或文件名用此方法上传, 此方法上传的文件有后缀
        ret = client.upload_by_buffer(content.read())  # 如果是通过文件的二进制数据上传的可以使用此方法,此方法上传的文件没有后缀

        # 判断是否上传成功
        if ret.get('Status') != 'Upload successed.':
            raise Exception('文件上传失败')

        return ret.get('Remote file_id')

    def exists(self, name):
        """
        判度上传的文件是否已经存在,如果存在就不上传了,不存在再调用save方法进行上传
        :param name: 要进行判断文件名
        :return: True(存在) / False(不存在)
        """
        return False  # 默认都上传

    def url(self, name):
        """
        当访问数据库image字段的url时会调用此方法的url拼接完整的url文件连接
        :param name: save方法返回的file_id
        :return: 返回完整的url文件路径 storage ip:端口 + file_id
        """
        return self.base_url + name


"""
{'Group name': 'group1',
 'Remote file_id': 'group1/M00/00/00/wKg0gFxNjkGAHO6TAACkT0APoxI269.jpg',
 'Status': 'Upload successed.',
 'Local file name': '/home/python/Desktop/shuju/01.jpg',
 'Uploaded size': '41.00KB',
 'Storage IP': '192.168.52.128'}

"""
