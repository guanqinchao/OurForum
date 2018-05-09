#coding:utf-8

"""
    likes app
"""
from django.conf.urls import include, url
from likes.views import *
#http://localhost:8000/likes/ + 
#在project的urls.py导入整个url配置
urlpatterns = [
    url(r'^likes_change$',likes_change,name='likes_change'),
    url(r'^likes_nums$',likes_nums,name='likes_nums'),
]
