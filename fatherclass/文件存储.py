from django.core.files.storage import Storage#继承django文件上传类
from fdfs_client.client import Fdfs_client
from django.conf import settings

class 文件存储类(Storage):
    '''fast dfs 文件存储类'''
    def __init__(self,client_conf=None,base_url=None):
        '''初始化'''
        if client_conf is None:
            client_conf =settings.FDFS_配置路径
        self.clent_conf=client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self,name, mode='rb'):
        '''打开文件是使用'''
        pass

    def _save(self,name, content):
        '''保存文件时使用'''
        #name是你选择的上传文件的名字
        # content就是包含你上传文件内容的文件对象

        #创建一个Fdfs文件对象,上传文件
        client=Fdfs_client(self.clent_conf)

        #上传文件至fast dfs 系统
        #upload_by_filename以文件名查找上传的文件
        #以文件内容查找上传文件
        ret=client.upload_appender_by_buffer(content.read())
        '''dict {
            'Group name'      : group_name,
            'Remote file_id'  : remote_file_id,
            'Status'          : 'Upload successed.',
            'Local file name' : '',
            'Uploaded size'   : upload_size,
            'Storage IP'      : storage_ip
        }'''
        if ret.get('Status') !='Upload successed.':
            #文件上传fdfs失败
            raise Exception('上传文件Fdfs失败')
        # 获取文件id
        #应该返回被保存文件的真实名称（通常是传进来的name，但是如果储存需要修改文件名称，则返回新的名称来代替）
        file_name=ret.get('Remote file_id')
        return file_name

    #如果提供的名称所引用的文件在文件系统中存在，则返回True，否则如果这个名称可用于新文件，返回False。
    def exists(self, name):
        '''django判断文件是否存在'''
        return False

    def url(self, name):
        '''返回可访问到文件的url路径'''
        return self.base_url+name