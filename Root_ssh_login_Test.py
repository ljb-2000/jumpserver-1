#!/usr/bin/env python
# coding:utf-8
import os
import sys
import salt.client
import time
#datetime用于生成每次执行的JOB ID
import datetime
#定义搜索错误日志模块
import re
#导入调用shell命令的模块
import pexpect
import json
#导入ssh远程连接测试模块
import commands
import paramiko
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jumpserver.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
from django.db.models import Q
from jasset.models import Asset, IDC, AssetGroup, ASSET_TYPE, ASSET_STATUS,AutoUpdataCI_Record,AssetRecord,cmdb_01
#导入平台加密模块
from jumpserver.api import *
####定义log模块-start
import logging
# create logger
logger_name = "log03"
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)

# create file handler
log_path = "/opt/jumpserver-master/logs/Root_ssh_login.log"
fh = logging.FileHandler(log_path)
fh.setLevel(logging.DEBUG)

# create formatter
fmt = "%(asctime)-15s %(levelname)s %(filename)s %(lineno)d %(module)s %(funcName)s %(process)d %(message)s"
datefmt = "%a %d %b %Y %H:%M:%S"
formatter = logging.Formatter(fmt, datefmt=None)

# add handler and formatter to logger
fh.setFormatter(formatter)
logger.addHandler(fh)

# print log info
# logger.debug('debug message')
# logger.info('info message')
# logger.warn('warn message')
# logger.error('error message')
# logger.critical('critical message')
from logging.handlers import RotatingFileHandler
#################################################################################################
#定义一个RotatingFileHandler，最多备份5个日志文件，每个日志文件最大10M
Rthandler = RotatingFileHandler('/opt/jumpserver-master/logs/Root_ssh_login.log', maxBytes=10*1024*1024,backupCount=5)
################################################################################################
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
#定义SSH连接检查模块
def getssh(hostname="127.0.0.1", port=22,username=None, password=None):
    status = -1; msg = None;

    try:
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(hostname, port, username=username, password=password, timeout=1)
        status = 0
    except paramiko.AuthenticationException, e:
        msg = e
    except:
        msg = 'SSH 连接错误!'
    finally:
        conn.close()

    return (status, msg)

#定义搜索每台主机执行是否有错误日志，则记录到数据库中
def RunLog_Check(hostname,filename,lines = 1,JOB_ID=20160404031502):
    #print the last several line(s) of a text file
    """
    Argument filename is the name of the file to print.
    Argument lines is the number of lines to print from last.
    """
    block_size = 1024
    block = ''
    nl_count = 0
    start = 0
    fsock = file(filename, 'rU')
    JOB_ID = str(JOB_ID)
    try:
        #seek to end
        fsock.seek(0, 2)
        #get seek position
        curpos = fsock.tell()
        while(curpos > 0): #while not BOF
            #seek ahead block_size+the length of last read block
            curpos -= (block_size + len(block));
            if curpos < 0: curpos = 0
            fsock.seek(curpos)
            #read to end
            block = fsock.read()
            nl_count = block.count('\n')
            #if read enough(more)
            if nl_count >= lines: break
        #get the exact start position
        for n in range(nl_count-lines+1):
            start = block.find('\n', start)+1
    finally:
        fsock.close()
    #print it out
    # print block[start:]

    r = re.compile(JOB_ID+':failed',re.M)
    nums = r.findall(block[start:])
    # print nums
    if len(nums):
        AutoUpdataCI_Record.objects.create(hostname=hostname, username="Salt-ssh_API", result="failed",job_id=JOB_ID)
    else:
        AutoUpdataCI_Record.objects.create(hostname=hostname, username="Salt-ssh_API", result="Success",job_id=JOB_ID)

#定义执行主模块
def Root_ssh_login_Test():
    """
    salt-ssh主执行模块，单台服务器执行，逐个命令执行，每条命令对应一条处理结果,记录发生改变的项
    :return:
    """
    #定义需要排除执行的主机
    except_ip = []
    ##获取asset表中没有安装salt-stack的服务器hostname列表(通过ci001字段的值为0进行过滤)
    asset_list_salt_ssh = cmdb_01.objects.filter(ci001__contains='0')
    asset_list = Asset.objects.all()
    # print asset_list_salt_ssh;
    for list_ip in asset_list:
        ip = list_ip.ip
        #获取当前系统的时间（级别到秒）,以记录每次执行的JOB_ID,格式为20160403234139
        now = datetime.datetime.now()
        JOB_ID01 = now.strftime("%Y%m%d%H%M%S")
        JOB_ID = "03_"+JOB_ID01
        if ip in except_ip:
            continue
        global asset_info
        info = []
        #通过以上获取的ip,查询asset列表中对应的root口令和密码
        print "ip_is:",ip
        #如果在资产表中没有查询到该主机的信息,则记录一个警告信息，然后进行下一次循环
        # try:
        #     asset_host = Asset.objects.get(ip__exact=ip)
        # except Asset.DoesNotExist:
        #     logger.warning("Asset not have that ip:%s:Asset_query_failed" % ip)
        #     continue
        log_user = list_ip.username
        passwd = list_ip.password
        passwd_text = CRYPTOR.decrypt(passwd)
        port = list_ip.port
        hostname = list_ip.hostname
        print "loguser:%s,passwd:%s,port:%s"%(log_user,passwd_text,port)
        try:
            #检查是否已部署ssh-key文件
            # cmdb_01_ssh_key = cmdb_01.objects.get(ip__exact=ip)
            # ssh_key_status = cmdb_01_ssh_key.ci002
            # print "ssh_key_status:%s:%s"%(ssh_key_status,ip)
            ssh_key_status = "0"
            if ssh_key_status == "0":
                print "Run ssh and key deploy proc"
                #通过ip,root用户,root密码，ssh远程登录连接测试
                (status, results) = getssh(hostname=str(ip),port=int(port),username=str(log_user),password=str(passwd_text))
                if status != 0:
                    print "ssh connect test failed:",ip
                    logger.warning("ssh_con_test_failed:%s" % ip)
                    continue
                else:
                    logger.info("ssh_con_test_suc:%s" % ip)
                    print "ssh_con_test_suc:%s",ip
                #自动部署ssh-key文件


        except Exception,e:
          logger.error("runcmd error %s" % e)
          print "run cmd error",e

Root_ssh_login_Test()