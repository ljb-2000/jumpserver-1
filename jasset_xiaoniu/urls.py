# coding:utf-8
from django.conf.urls import patterns, include, url
from jasset_xiaoniu.views import *

urlpatterns = patterns('',
    url(r'^group_xiaoniu/del/$', group_del_xiaoniu, name='asset_group_del_xiaoniu'),
    url(r'^group_xiaoniu/add/$', group_add_xiaoniu, name='asset_group_add_xiaoniu'),
    url(r'^group_xiaoniu/list/$', group_list_xiaoniu, name='asset_group_list_xiaoniu'),
    url(r'^group_xiaoniu/edit/$', group_edit_xiaoniu, name='asset_group_edit_xiaoniu'),
)