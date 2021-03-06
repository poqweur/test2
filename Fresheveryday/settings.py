"""
Django settings for Fresheveryday project.

Generated by 'django-admin startproject' using Django 1.8.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
'''导入apps模块路径'''
sys.path.append(os.path.join(BASE_DIR,'apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'pq=h=$52ync+gpyzijjgs^7##pz*@_&bl&vi$hh0jmwk7ugdv9'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False #是否是调试模式false是正式上线

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #调用富文本模块
    'tinymce',
    'haystack',#全文检索框架
    'User',#导入apps模块后模块内的应用没有提示
    'cart',
    'goods',
    'order'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'Fresheveryday.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Fresheveryday.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'Fresheveryday',
        'PORT':3306,
        'HOST':'127.0.0.1',
        'USER':'root',
        'PASSWORD':'mysql',
    }
}

AUTH_USER_MODEL = 'User.User'#必须保证自定义user必须是在第一次迁移中创建的表
# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS= [os.path.join(BASE_DIR,'static')]
#配置收集静态文件路径在家目录下
#python manage.py collectstatic
STATIC_ROOT='/var/www/Fresheveryday/static'

#设置富文本
TINYMCE_DEFAULT_CONFIG={
    'theme':'advanced',
    'width':600,
    'heigth':400,
}
#创建邮箱连接
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25
#发送邮件的邮箱
EMAIL_HOST_USER = '15210220793@163.com'
#在邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = 'wjy198981'
#收件人看到的发件人
EMAIL_FROM = '15210220793@163.com'
EMAIL_USE_TLS = True#qq需要设置成True否则会失败,其他邮箱可以是False


# session使用配置cache写入缓存中
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

#设置django缓存redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
# 如果用户没有登入，则重定向到settings.LOGIN_URL
LOGIN_URL='/user/login'


#设置django默认文件存储类,默认的Storage 类，用于没有指定文件系统的任何和文件相关的操作
DEFAULT_FILE_STORAGE='fatherclass.文件存储.文件存储类'
#设置fast dfs 客户端配置文件路径
FDFS_配置路径='./fatherclass/client.conf'
#设置fast dfs 文件存储服务器上的nginx的ip和端口
FDFS_URL='http://192.168.109.131:8888/'

#全文检索框架的配置
HAYSTACK_CONNECTIONS = {
    'default': {
        #使用whoosh引擎'ENGINE'后是搜索引擎
        'ENGINE': 'haystack.backends.whoosh_cn_backend.WhooshEngine',
        #索引文件路径
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
    }
}
#当添加、修改、删除数据时，自动生成索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'