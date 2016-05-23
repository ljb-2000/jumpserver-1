#!/usr/bin/env python
# coding:utf-8
import os
import sys
import time
#datetime用于生成每次执行的JOB ID
import datetime
#定义搜索错误日志模块
import re
#导入调用shell命令的模块
import json
#导入拷贝包
import copy

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jumpserver.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
from django.db.models import Q
from jasset.models import Asset, IDC, AssetGroup, ASSET_TYPE, ASSET_STATUS,AutoUpdataCI_Record,AssetRecord,cmdb_01,AssetRelation,AssetRelationNet,CompanyName,DepartmentName,BusinessName

#自定义数据库获取接口
def get_object(model, **kwargs):
    """
    use this function for query
    使用改封装函数查询数据库
    """
    for value in kwargs.values():
        if not value:
            return None

    the_object = model.objects.filter(**kwargs)
    if len(the_object) == 1:
        the_object = the_object[0]
    else:
        the_object = None
    return the_object
#定义查询主模块
def AssetRelationGenration():
    """
    查询每条服务器的公司，部门，业务记录，生成一个记录表
    :return:
    """
    #定义需要排除执行的主机
    #except_ip = [u'192.168.0.11', u'192.168.0.12',u'10.10.16.146', u'10.10.16.233', u'10.10.16.11', u'10.10.16.130', u'10.10.16.138', u'10.10.16.139', u'10.10.16.141', u'10.10.16.143', u'10.10.16.145', u'10.10.16.146', u'10.10.16.147', u'10.10.16.148', u'10.10.16.149', u'10.10.16.154', u'10.10.16.156', u'10.10.16.164', u'10.10.16.167', u'172.17.42.1', u'10.10.16.171', u'10.10.16.173', u'10.10.16.175', u'10.10.16.180', u'10.10.16.201', u'10.10.16.205', u'10.10.16.221', u'10.10.16.223', u'10.10.16.225', u'10.10.16.227', u'10.10.16.230', u'10.10.16.235', u'10.10.16.250', u'10.10.16.140', u'10.10.16.170', u'10.10.16.169', u'10.10.16.120', u'10.10.16.121', u'10.10.16.122']
    except_ip = [u'10.10.16.239', u'10.10.16.231']
    list_run_ip = [u'192.168.0.11', u'192.168.0.12']
    ##获取cmdb_01表中没有安装salt-stack的服务器hostname列表(通过ci001字段的值为0进行过滤)
    # asset_list_salt_ssh = cmdb_01.objects.filter(ci001__contains='0')
    asset_list = Asset.objects.all()
    #循环读取列表
    for list_ip in asset_list:
        ip = list_ip.ip
        #判断是否在执行列表中
        if ip in list_run_ip:
            # if True:
            #判断是否是排除执行的主机
            if ip in except_ip:
                continue
            #通过以上获取的ip,查询asset列表中对应的root口令和密码
            print "ip_is:",ip
            #如果在资产表中没有查询到该主机的信息,则记录一个警告信息，然后进行下一次循环
            # try:
            #     asset_host = Asset.objects.get(ip__exact=ip)
            # except Asset.DoesNotExist:
            #     logger.warning("Asset not have that ip:%s:Asset_query_failed" % ip)
            #     continue
            company_name = get_object(CompanyName, id=list_ip.id)
            department_name = get_object(DepartmentName, id=list_ip.id)
            business_name = get_object(BusinessName, id=list_ip.id)
            print "company_name",company_name
            print "department_name",department_name
            print "business_name",business_name
            hash_char = str(company_name)+str(department_name)+str(business_name)
            print "hash_char",hash_char
            #查询是否已存在该关系
            judgment_rel = get_object(AssetRelation,Relation_id=hash_char)
            if judgment_rel == None:
                AssetRelation.objects.create(company_name=company_name, department_name=department_name, business_name=business_name,Relation_id=hash_char)
def AssetRelationGenerationNet():
    """
    查询AssetRelationGen生成一个树结构节点的信息表
    :return:
    """
    #清空关系网表
    AssetRelationNet.objects.all().delete()
    #获取关系列表
    relation = AssetRelation.objects.all()
    # relation = AssetRelation.objects.filter(id=1)
    #定义存储数组
    data = []
    #初始化节点值，该值不能重复
    node_id = 1;
    for relation_list in relation:
        company_name = relation_list.company_name
        department_name = relation_list.department_name
        business_name = relation_list.business_name
        business_name_url = "<a href='/jasset/asset/list/?company_name=%s&department_name=%s&business_name=%s'>%s</a>"%(company_name,department_name,business_name,business_name)
        print "business_name_url",business_name_url
        num_id = relation_list.id
        print "num_id:",num_id
        #每一行AssetRelation表的记录对应AssetRelationNet表有3条记录
        #组装NAME的信息为一个列表
        name_list = [company_name,department_name,business_name_url]
        #定义每个节点的字典信息
        depth_dict = {}
        #定义每条树的父节点信息和层次结构信息
        parent_id = 0;depth = 1;
        for name in  name_list:
            # for num in range(len(name_list)):
            depth_dict['id'] = str(node_id)
            depth_dict['name'] = name
            depth_dict['parent_id'] = str(parent_id)
            depth_dict['depth'] = str(depth)
            # for key,value in depth_dict.iteritems():
            #     print "key is:%s:value is:%s"%(key,value)
            data.append(depth_dict.copy())
            parent_id = node_id;node_id = node_id + 1;depth = depth + 1
            AssetRelationNet.objects.create(node_id=depth_dict['id'],name=depth_dict['name'],parent_id=depth_dict['parent_id'],depth=depth_dict['depth'])
        #生成第2条记录的节点信息,公司节点的parent_id要为0,但node_id需要紧接上层的node_id或者不能与上层ID重复即可,可以以21数字开头
    # for data_list in data:
    #     for key02,value02 in data_list.iteritems():
    #         print "key02 is:%s:value02 is:%s"%(key02,value02)
    #去掉重复的公司和部门名称
    #先去掉重复的公司名称
    print_num = 0
    # for i in range(len(data)-1):
    #     if data[i]['depth'] == '2':
    #         print "data[i]['name']:",data[i]['name']
    #         for key02,value02 in data[i].iteritems():
    #             print "key02 is:%s:value02 is:%s",key02,value02
    #
    #     else:
    #         continue
    for i in range(len(data)):
        print "i:",i
        if data[i]['depth'] == '1':
            # print "data[i]['name']:",data[i]['name']
            for key02,value02 in data[i].iteritems():
                # print "key02 is:%s:value02 is:%s",key02,value02
                if key02 == 'name':
                    h = i + 1
                    print "before_h:",h
                    for h in range(h,len(data)):
                        print "after_h:",h
                        if data[h]['depth'] == '1':
                            for key03,value03 in data[h].iteritems():
                                if data[i]['name'] == data[h]['name']:
                                    data[h]['parent_id'] = data[i]['parent_id']
                                # print "data[i]['name']",data[i]['name']
                                # print "data[h]['name']",data[h]['name']
                                # print "i:",i
                                # print "h:",h

        else:
            pass

    print "data_len:",len(data)
    return data


# AssetRelationGenration()
AssetRelationGenerationNet()