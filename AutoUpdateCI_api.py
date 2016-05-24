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
#导入ini文件解析模块,用于
import ConfigParser
# 导入 smtplib 和 MIMEText
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jumpserver.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
from django.db.models import Q
from jasset.models import Asset, IDC, AssetGroup, ASSET_TYPE, ASSET_STATUS,AutoUpdataCI_Record,AssetRecord
####定义log模块-start
import logging
# create logger
logger_name = "log01"
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)

# create file handler
log_path = "/opt/jumpserver-master/logs/AutoUpdateCI.log"
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
# logger.info('error message')
# logger.critical('critical message')
from logging.handlers import RotatingFileHandler
#################################################################################################
#定义一个RotatingFileHandler，最多备份5个日志文件，每个日志文件最大10M
Rthandler = RotatingFileHandler('/opt/jumpserver-master/logs/AutoUpdateCI.log', maxBytes=10*1024*1024,backupCount=5)
################################################################################################
####定义log模块-End
#定义CI信息存储字典
asset_dict = {'ETH0_IP': '', 'ETH0_MAC': '', 'OSType': '','CPUType':'','MEMSize':'','DISKSize':''};

#定义各个CI的获取命令
ETH0_IP = "ifconfig eth0|awk '/inet addr/ {print $2}'|cut -d ':' -f 2"
ETH0_MAC = "ifconfig eth0 | awk '/HWaddr/ {print $5}'"
OSType = "cat /etc/redhat-release"
CPUType = "cat /proc/cpuinfo   |grep 'model name'|uniq | awk '{print $4$5$6$8$9}'"
MEMSize = "cat /proc/meminfo  | grep 'MemTotal'|awk '{print $2$3}'"
DISKSize = "fdisk -l |awk '/Disk \/dev\/sd/ {print $3$4}'|cut -d , -f 1"
#定义hostname输出结果处理函数
def cmd_hostname_res_func(cmd_hostname_res):
    """
    定义hostname的输出结果
    """
    if cmd_hostname_res == None:
        return None
    return cmd_hostname_res.strip("\n")
#定义内核版本输出结果处理函数
def cmd_kernel_rel_res_func(cmd_kernel_rel_res):
    """
    定义内核版本的输出结果
    """
    if cmd_kernel_rel_res == None:
        return None
    return cmd_kernel_rel_res.strip("\n")
def cmd_eth0_ip_res_func(cmd_eth0_ip_res,hostname,JOB_ID):
    """
    定义eht0 ip输出结果
    """
    if cmd_eth0_ip_res == None:
        return None
    matchObj = re.search(r'inet addr:(?<![\.\d])(?:\d{1,3}\.){3}\d{1,3}(?![\.\d])',cmd_eth0_ip_res,re.M|re.I)
    if matchObj == None:
        logger.warning("cmd_eth0_ip:res func:%s:%s:warning:",hostname,JOB_ID)
        return None
    else:
        eth0_ip = matchObj.group().split(":")[1]
        return eth0_ip
def cmd_eth0_mac_res_func(cmd_eth0_mac_res):
    """
    定义eht0 mac输出结果
    """
    if cmd_eth0_mac_res == None:
        return None
    eth0_mac = cmd_eth0_mac_res.split()[4]
    return eth0_mac
def cmd_ostype_res_func(cmd_ostype_res):
    """
    定义ostype输出结果
    """
    # matchObj = re.search(r'Description:(.*?) .*',cmd_ostype_res,re.M|re.I)
    # ostype = matchObj.group().split(":")[1].strip()
    if cmd_ostype_res == None:
        return None
    ostype = cmd_ostype_res.replace("\n","")
    return ostype
def cmd_cputype_res_func(cmd_cputype_res):
    """
    定义cputype输出结果
    """
    if cmd_cputype_res == None:
        return None
    matchObj = re.search(r'model name(.*?) .*',cmd_cputype_res,re.M|re.I)
    cputype = matchObj.group().split(":")[1].strip().replace(" ","")
    return cputype
def cmd_memsize_res_func(cmd_memsize_res):
    """
    定义memsize输出结果
    """
    if cmd_memsize_res == None:
        return None
    memsize = cmd_memsize_res.strip("\n").split()[1]
    print "memsize:",memsize
    memsize_01 = round((float(memsize) / 1000) / 1000,0)
    memsize_format = unicode(memsize_01)
    return memsize_format
def cmd_disksize_res_func(cmd_disksize_res):
    """
    计算disk输出的总和
    """
    if cmd_disksize_res == None:
        return None
    #计算sda的磁盘容量
    match_fdisk_sda = re.search(r'/dev/sda:(.*?) .*',cmd_disksize_res,re.M|re.I)
    sda_sum = 0.0
    if match_fdisk_sda != None:
        sda_sum = match_fdisk_sda.group().split()[1]
    #计算sdb的磁盘容量
    match_fdisk_sdb = re.search(r'/dev/sdb:(.*?) .*',cmd_disksize_res,re.M|re.I)
    sdb_sum = 0.0
    if match_fdisk_sdb != None:
         sdb_sum = match_fdisk_sdb.group().split()[1]
    #计算sdc的磁盘容量
    sdc_sum = 0.0
    match_fdisk_sdc = re.search(r'/dev/sdc:(.*?) .*',cmd_disksize_res,re.M|re.I)
    if match_fdisk_sdc != None:
        sdc_sum = match_fdisk_sdc.group().split()[1]
    disk_all = round(float(sda_sum) + float(sdb_sum) +float(sdc_sum),0)
    return str(disk_all)
def cmd_cpunum_res_func(cmd_cpunum_res):
    """
    :param 计算虚拟CPU的个数
    :return:
    """
    if cmd_cpunum_res == None:
        return None
    cpu_num = unicode(cmd_cpunum_res.replace("\n",""))
    return cpu_num
#定义命令异步执行模块
Runner = salt.client.LocalClient()
def cmdRun_fuc(asset_id,command,JOB_ID,hostname):
    Response = Runner.cmd_async(asset_id,'cmd.run',[command])
    logger.info("%s:Run cmd:%s:%s:Start:",command,hostname,JOB_ID)
    return Response
#定义异步执行命令结果获取执行结果
def cmdRun_result(asset_id,TIME_OUT,JID,command,JOB_ID,hostname):
    t = 0;
    while not Runner.get_cache_returns(JID):
       time.sleep(1)
       if t == TIME_OUT:
           logger.warning("%s:Run cmd:%s:%s:failed:",command,hostname,JOB_ID)
           # logger.info("%s:Run cmd:%s:%s:End:",command,hostname,JOB_ID)
           return None
       else:
           t = t+ 1
    Runner_ret = Runner.get_cache_returns(JID)
    logger.info("%s:Run cmd:%s:%s:Success:",command,hostname,JOB_ID)
    return Runner_ret[asset_id]['ret']

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
#定义搜索每台主机执行是否有错误日志，则记录到数据库中
def RunLog_Check(hostname,filename,lines = 1,JOB_ID=20160404031502,MAIN_TASK_JOB_ID=0320160505111605):
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
        AutoUpdataCI_Record.objects.create(hostname=hostname, username="Saltstack_API", result="failed",job_id=JOB_ID,main_task_id=MAIN_TASK_JOB_ID)
    else:
        AutoUpdataCI_Record.objects.create(hostname=hostname, username="Saltstack_API", result="Success",job_id=JOB_ID,main_task_id=MAIN_TASK_JOB_ID)
# 发送邮件函数
def send_mail(to_list, sub,email_body_file):
    #定义发送列表
    mailto_list=["342304628@qq.com"]
    # 设置服务器名称、用户名、密码以及邮件后缀
    mail_host = "smtp.xiaoniu66.com:25"
    mail_user = "ouyangbin@xiaoniu66.com"
    mail_pass = "oyb,p@ssw0rd"
    mail_postfix="xiaoniu66.com"
    # mail_body_cotent = "/opt/jumpserver-master/email_body_salt-api.ini"
    me = mail_user + "<"+mail_user+"@"+mail_postfix+">"
    fp = open(email_body_file)
    msg = MIMEText(fp.read(),_charset="utf-8")
    fp.close()
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    try:
        send_smtp = smtplib.SMTP()
        send_smtp.connect(mail_host)
        send_smtp.login(mail_user, mail_pass)
        send_smtp.sendmail(me, to_list, msg.as_string())
        send_smtp.close()
        return True
    except Exception, e:
        print str(e)
        return False
#定义email发生信息获取
def send_email_inf_func(MAIN_TASK_JOB_ID):
    """
    :param 获取邮件发送列表，组装邮件发送信息，逐个发送邮件
    :return:
    """
    change_list = AssetRecord.objects.filter(main_task_id__contains=MAIN_TASK_JOB_ID)
    for list_email in change_list:
        if list_email.email:
            host_inf = Asset.objects.get(id__exact=list_email.asset_id)
            hostname = host_inf.hostname
            ip = host_inf.ip
            email_body = list_email.content
            email_sub = "[CMDB_CI UPdate]:%s" % hostname
            print "send email hostname:",hostname
            print "send email ip:",ip
            print "send email email_body:",email_body
            print "email addr:",list_email.email
            print "email sub:",email_sub
            #已经获取到该服务器的所有变更CI信息
            #判断哪些CI项发生改变需要
            change_list_ci = eval(str(email_body))
            #清空该文件的内容,以重新写入
            email_body_file = "/opt/jumpserver-master/email_body_salt-api.ini"
            cfgfile = open(email_body_file,'w')
            cfgfile.truncate()
            cfgfile.close()
            #配置ini文件，将hostname修改的项写入到文件
            cfgfile = open(email_body_file,'w')
            Config = ConfigParser.ConfigParser()
            Config.add_section(hostname)
            Config.write(cfgfile)
            cfgfile.close()
            for index in range(len(change_list_ci)):
                if change_list_ci[index][0] == u'主机名':
                    print "old_hostname",change_list_ci[index][1]
                    old_hostname = change_list_ci[index][1]
                    print "new_hostname",change_list_ci[index][2]
                    new_hostname = change_list_ci[index][2]
                    #配置ini文件，将CI修改的项写入到文件
                    cfgfile = open(email_body_file,'w')
                    change_mem = "old_hostname:%s:new_hostname:%s" % (old_hostname,new_hostname)
                    Config.set(hostname,"HostName",change_mem)
                    Config.write(cfgfile)
                    cfgfile.close()
                if change_list_ci[index][0] == u'主机IP':
                    print "old_ip",change_list_ci[index][1]
                    old_ip = change_list_ci[index][1]
                    print "new_ip",change_list_ci[index][2]
                    new_ip = change_list_ci[index][2]
                    #配置ini文件，将CI修改的项写入到文件
                    cfgfile = open(email_body_file,'w')
                    change_mem = "old_ip:%s:new_ip:%s" % (old_ip,new_ip)
                    Config.set(hostname,"IPAddre_eth0",change_mem)
                    Config.write(cfgfile)
                    cfgfile.close()
                if change_list_ci[index][0] == u'内存':
                    print "old_mem",change_list_ci[index][1]
                    old_mem = change_list_ci[index][1]
                    print "new_mem",change_list_ci[index][2]
                    new_mem = change_list_ci[index][2]
                    #配置ini文件，将CI修改的项写入到文件
                    cfgfile = open(email_body_file,'w')
                    change_mem = "old_mem size:%s:new_mem size:%s" % (old_mem,new_mem)
                    Config.set(hostname,"MemSize",change_mem)
                    Config.write(cfgfile)
                    cfgfile.close()
                if change_list_ci[index][0] == u'MAC地址':
                    print "old_mac",change_list_ci[index][1]
                    old_mac = change_list_ci[index][1]
                    print "new_mac",change_list_ci[index][2]
                    new_mac = change_list_ci[index][2]
                    #配置ini文件，将CI修改的项写入到文件
                    cfgfile = open(email_body_file,'w')
                    change_mac = "old_mac size:%s:new_mac size:%s" % (old_mac,new_mac)
                    Config.set(hostname,"MAC_Addr",change_mac)
                    Config.write(cfgfile)
                    cfgfile.close()
                if change_list_ci[index][0] == u'CPU':
                    print "old_cpu",change_list_ci[index][1]
                    old_cpu = change_list_ci[index][1]
                    print "new_cpu",change_list_ci[index][2]
                    new_cpu = change_list_ci[index][2]
                    #配置ini文件，将CI修改的项写入到文件
                    cfgfile = open(email_body_file,'w')
                    change_cpu = "old_cpu num:%s:new_cpu num:%s" % (old_cpu,new_cpu)
                    Config.set(hostname,"CPU_Num",change_cpu)
                    Config.write(cfgfile)
                    cfgfile.close()
                if change_list_ci[index][0] == u'硬盘':
                    print "old_disksize",change_list_ci[index][1]
                    old_disksize = change_list_ci[index][1]
                    print "new_disksize",change_list_ci[index][2]
                    new_disksize = change_list_ci[index][2]
                    #配置ini文件，将CI修改的项写入到文件
                    cfgfile = open(email_body_file,'w')
                    change_disksize = "old_disksize:%s:new_disksize:%s" % (old_disksize,new_disksize)
                    Config.set(hostname,"DiskSize",change_disksize)
                    Config.write(cfgfile)
                    cfgfile.close()
            #该服务器的所有CI项写入文件之后，再进行邮件发送
            #判断是否有写入CI项，若没有，则不发送邮件
            option_check = Config.options(hostname)
            if option_check:
                send_mail(list_email.email, email_sub,email_body_file)

        else:
            logger.warning("AutoUpdateRun_salt_ssh:email accout is Null:%s:%s:",list_email.hostname,list_email.asset_id,MAIN_TASK_JOB_ID)

#开始执行命令
#需排除的主机
def AutoUpdateRun():
    #定义需要排除执行的主机
    except_hostname = ["centos01.xiaoniu66.com","centos03.xiaoniu66.com",]
    #定义需要排除执行的主机
    #except_ip = [u'192.168.0.11', u'192.168.0.12',u'10.10.16.146', u'10.10.16.233', u'10.10.16.11', u'10.10.16.130', u'10.10.16.138', u'10.10.16.139', u'10.10.16.141', u'10.10.16.143', u'10.10.16.145', u'10.10.16.146', u'10.10.16.147', u'10.10.16.148', u'10.10.16.149', u'10.10.16.154', u'10.10.16.156', u'10.10.16.164', u'10.10.16.167', u'172.17.42.1', u'10.10.16.171', u'10.10.16.173', u'10.10.16.175', u'10.10.16.180', u'10.10.16.201', u'10.10.16.205', u'10.10.16.221', u'10.10.16.223', u'10.10.16.225', u'10.10.16.227', u'10.10.16.230', u'10.10.16.235', u'10.10.16.250', u'10.10.16.140', u'10.10.16.170', u'10.10.16.169', u'10.10.16.120', u'10.10.16.121', u'10.10.16.122']
    except_ip = []
    #list_run_ip = [u'192.168.0.11', u'192.168.0.12',u'10.10.16.146',u'10.10.16.11',u'10.10.16.138',u'10.10.16.141',u'10.10.16.143',u'10.10.16.145',u'10.10.16.148',u'10.10.16.149',u'10.10.16.154',u'10.10.16.156',u'10.10.16.164',u'10.10.16.173',u'10.10.16.175',u'10.10.16.180',u'10.10.16.205',u'10.10.16.221',u'10.10.16.223',u'10.10.16.225',u'10.10.16.227',u'10.10.16.230',u'10.10.16.235',u'10.10.16.250',u'10.10.16.140',u'10.10.16.170',u'10.10.16.120',u'10.10.16.121']
    list_run_ip = [u'192.168.0.11', u'192.168.0.12',u'10.10.16.146']
    #从jumpserver数据库资产表中获取服务器列表
    asset_list = Asset.objects.all()
    # print asset_list;
    #定义主任务执行JOB ID
    now = datetime.datetime.now()
    MAIN_TASK_JOB_ID01 = now.strftime("%Y%m%d%H%M%S")
    MAIN_TASK_JOB_ID = "04_"+MAIN_TASK_JOB_ID01
    logger.info("AutoUpdateRun_salt_api:main_task_job:%s:Start:",MAIN_TASK_JOB_ID)
    for list_h in asset_list:
        ip = list_h.ip;
        #获取当前系统的时间（级别到秒）,以记录每次执行的JOB_ID,格式为20160403234139
        now = datetime.datetime.now()
        JOB_ID01 = now.strftime("%Y%m%d%H%M%S")
        JOB_ID = "01_"+JOB_ID01
        #判断是否在执行列表中
        if ip in list_run_ip:
            #判断是否在排除的主机列表中
            if ip in except_ip:
                continue
            global asset_info
            info = []
            #获取该主机对应的ID
            id = list_h.id
            asset_id = str(id)
            hostname = list_h.hostname
            try:
                #获取服务器的hostname:CI01
                cmd_hostname_bash = "hostname"
                res_HOSTNAME_JID = cmdRun_fuc(asset_id,cmd_hostname_bash,JOB_ID,hostname)
                res_HOSTNAME = cmdRun_result(asset_id,4,res_HOSTNAME_JID,cmd_hostname_bash,JOB_ID,hostname)
                asset_dict['HOSTNAME'] = cmd_hostname_res_func(res_HOSTNAME)
                print asset_dict['HOSTNAME']

                #获取服务器的内核版本:CI02
                cmd_kernel_rel_bash = "uname -r"
                res_KERNEL_REL_JID = cmdRun_fuc(asset_id,cmd_kernel_rel_bash,JOB_ID,hostname)
                res_KERNEL = cmdRun_result(asset_id,4,res_KERNEL_REL_JID,cmd_kernel_rel_bash,JOB_ID,hostname)
                asset_dict['KERNEL_VER'] = cmd_kernel_rel_res_func(res_KERNEL)
                print asset_dict['KERNEL_VER']

                #获取eth0网卡的IP和MAC地址:CI03 CI04
                cmd_eth0_ip_bash = "ifconfig -a | head -n 8"
                res_ETH0_IP_JID = cmdRun_fuc(asset_id,cmd_eth0_ip_bash,JOB_ID,hostname)
                res_ETH0_IP = cmdRun_result(asset_id,4,res_ETH0_IP_JID,cmd_eth0_ip_bash,JOB_ID,hostname)
                asset_dict['ETH0_IP'] = cmd_eth0_ip_res_func(res_ETH0_IP,hostname,JOB_ID)
                asset_dict['ETH0_MAC'] = cmd_eth0_mac_res_func(res_ETH0_IP)
                print asset_dict['ETH0_IP']
                print asset_dict['ETH0_MAC']

                #获取系统的OSType:CI05
                #输出结果为:CentOS release 6.5 (Final)
                cmd_ostype_bash = "cat /etc/redhat-release"
                res_OSType_JID = cmdRun_fuc(asset_id,cmd_ostype_bash,JOB_ID,hostname)
                res_OSType = cmdRun_result(asset_id,4,res_OSType_JID,cmd_ostype_bash,JOB_ID,hostname)
                asset_dict['OSType'] =cmd_ostype_res_func(res_OSType)
                print asset_dict['OSType']

                 #获取系统的CPUType:CI06
                #输出结果为:Intel(R)Core(TM)i5-4590@3.30GHz
                cmd_cputype_bash = "cat /proc/cpuinfo"
                res_CPUType_JID = cmdRun_fuc(asset_id,cmd_cputype_bash,JOB_ID,hostname)
                res_CPUType = cmdRun_result(asset_id,4,res_CPUType_JID,cmd_cputype_bash,JOB_ID,hostname)
                asset_dict['CPUType'] =cmd_cputype_res_func(res_CPUType)
                print asset_dict['CPUType']

                #获取系统的MEMSize:CI07
                #输出结果为:676732kB
                cmd_memsize_bash = "cat /proc/meminfo  | grep MemTotal"
                res_MEMSize_JID = cmdRun_fuc(asset_id,cmd_memsize_bash,JOB_ID,hostname)
                res_MEMSize = cmdRun_result(asset_id,4,res_MEMSize_JID,cmd_memsize_bash,JOB_ID,hostname)
                asset_dict['MEMSize'] =cmd_memsize_res_func(res_MEMSize)
                print asset_dict['MEMSize']

                #获取系统的DISKSize:CI08
                #输出结果为:300.0GB
                cmd_disksize_bash = "fdisk -l"
                res_DISKSize_JID = cmdRun_fuc(asset_id,cmd_disksize_bash,JOB_ID,hostname)
                res_DISKSize = cmdRun_result(asset_id,4,res_DISKSize_JID,cmd_disksize_bash,JOB_ID,hostname)
                asset_dict['DISKSize'] =cmd_disksize_res_func(res_DISKSize)
                print asset_dict['DISKSize']

                #获取系统的虚拟CPU的个数:CI09
                #输出结果为:2
                cmd_cpunum_bash = "cat /proc/cpuinfo |grep process|wc -l"
                res_CPUNum_JID = cmdRun_fuc(asset_id,cmd_cpunum_bash,JOB_ID,hostname)
                res_CPUNum = cmdRun_result(asset_id,4,res_CPUNum_JID,cmd_cpunum_bash,JOB_ID,hostname)
                asset_dict['CPUNum'] =cmd_cpunum_res_func(res_CPUNum)
                print asset_dict['CPUNum']

                #记录这台主机的本次命令执行结果成功或失败
                RunLog_Check(hostname,"/opt/jumpserver-master/logs/AutoUpdateCI.log",20,JOB_ID,MAIN_TASK_JOB_ID)
                #获取数据库中这台主机的CI项
                asset_old = get_object(Asset, hostname=hostname)
                # print "that hostname ip is:",asset_old.ip
                # print "that hostname disk is:",asset_old.disk
                asset_old_dict = {'HOSTNAME':'','KERNEL_VER':'','ETH0_IP_old': '', 'ETH0_MAC_old': '', 'OSType_old': '','CPUType_old':'','MEMSize_old':'','DISKSize_old':''}
                asset_old_dict['HOSTNAME'] = asset_old.hostname
                # asset_old_dict['KERNEL_VER'] = asset_old.system_version
                asset_old_dict['ETH0_IP_old'] = asset_old.ip
                asset_old_dict['ETH0_MAC_old'] = asset_old.mac
                asset_old_dict['OSType_old'] = asset_old.system_type
                asset_old_dict['CPUType_old'] = asset_old.cpu
                asset_old_dict['MEMSize_old'] = asset_old.memory
                asset_old_dict['DISKSize_old'] = asset_old.disk
                #对比这台服务器所有的CI项，如果一样，则进行下一台服务器更新
                cmp_result = cmp(asset_dict,asset_old_dict)
                if cmp_result == 0:
                    continue
                #对比每个CI项
                #先对新收集的CI结果进行检查，如果为空，则不进行对比和更新
                #定义一个用于记录配置修改的列表
                alert_list = []
                if asset_dict['HOSTNAME']:
                    if asset_dict['HOSTNAME'] != asset_old_dict['HOSTNAME']:
                        #先记录旧的CI配置，然后再把新的配置替换旧的配置
                        alert_list.append([u"主机名",asset_old_dict['HOSTNAME'],asset_dict['HOSTNAME']])
                        #将新CI配置赋值给旧的配置
                        asset_old.hostname =  asset_dict['HOSTNAME']
                # if asset_dict['KERNEL_VER']:
                #     if asset_dict['KERNEL_VER'] != asset_old_dict['KERNEL_VER']:
                #         #先记录旧的CI配置，然后再把新的配置替换旧的配置
                #         alert_list.append([u"系统版本号",asset_old_dict['KERNEL_VER'],asset_dict['KERNEL_VER']])
                #         #将新CI配置赋值给旧的配置
                #         asset_old.system_version =  asset_dict['KERNEL_VER']
                if asset_dict['ETH0_IP']:
                    if asset_dict['ETH0_IP'] != asset_old_dict['ETH0_IP_old']:
                        #先记录旧的CI配置，然后再把新的配置替换旧的配置
                        alert_list.append([u"主机IP",asset_old_dict['ETH0_IP_old'],asset_dict['ETH0_IP']])
                        #将新CI配置赋值给旧的配置
                        asset_old.ip =  asset_dict['ETH0_IP']
                if asset_dict['ETH0_MAC']:
                    if asset_dict['ETH0_MAC'] != asset_old_dict['ETH0_MAC_old']:
                        alert_list.append([u"MAC地址",asset_old_dict['ETH0_MAC_old'],asset_dict['ETH0_MAC']])
                        asset_old.mac = asset_dict['ETH0_MAC']
                if asset_dict['OSType']:
                    if asset_dict['OSType'] != asset_old_dict['OSType_old']:
                        alert_list.append([u"系统类型",asset_old_dict['OSType_old'],asset_dict['OSType']])
                        asset_old.system_type = asset_dict['OSType']
                #判断cpu和cputype的执行命令输出是否为None,若为Noe,则不赋值
                if asset_dict['CPUType'] != None and asset_dict['CPUNum'] != None:
                    asset_dict['CPU'] = asset_dict['CPUType']+ ' * ' +asset_dict['CPUNum']
                    print "asset_dict['CPU']",asset_dict['CPU']
                else:
                    asset_dict['CPU'] = None
                    print "asset_dict['CPU']",asset_dict['CPU']

                if asset_dict['CPU']:
                    if asset_dict['CPU'] != asset_old_dict['CPUType_old']:
                        alert_list.append([u"CPU",asset_old_dict['CPUType_old'],asset_dict['CPU']])
                        asset_old.cpu = asset_dict['CPU']
                if asset_dict['MEMSize']:
                    if asset_dict['MEMSize'] != asset_old_dict['MEMSize_old']:
                        alert_list.append([u"内存",asset_old_dict['MEMSize_old'],asset_dict['MEMSize']])
                        asset_old.memory = asset_dict['MEMSize']
                if asset_dict['DISKSize']:
                    if asset_dict['DISKSize'] != asset_old_dict['DISKSize_old']:
                        alert_list.append([u"硬盘",asset_old_dict['DISKSize_old'],asset_dict['DISKSize']])
                        asset_old.disk = asset_dict['DISKSize']
                #对比完成之后更新asset数据表
                asset_old.save()
                #对比完成之后将修改的CI记录更新到asset_record表中
                if alert_list:
                    AssetRecord.objects.create(asset=asset_old, username="Saltstack_API", content=alert_list,job_id=JOB_ID,main_task_id=MAIN_TASK_JOB_ID,email=asset_old.email)
                #在完成本次主机的更新和对比之后，进行数据清空
                asset_dict.clear()
                asset_old_dict.clear()
                del alert_list[:]
            except Exception,e:
              logger.error("runcmd error %s" % e)
              #记录这台主机的本次命令执行结果成功或失败
              RunLog_Check(hostname,"/opt/jumpserver-master/logs/AutoUpdateCI.log",20,JOB_ID,MAIN_TASK_JOB_ID)
              print "run cmd error",e
    logger.info("AutoUpdateRun_salt_api:main_task_job:%s:End:",MAIN_TASK_JOB_ID)
    send_email_inf_func(MAIN_TASK_JOB_ID)

def RunSche():
    while True:
        #获取系统当前时间,年月日，时分秒
        import datetime
        import time
        #定义用户计划运行的时间
        #用户定义年,格式input_year = "2016,2017"
        input_year = "2016,2017"
        #用户定义单个月，格式input_month = "4"
        #用户定义多个月，格式input_month = "4,5"
        input_month = "4"
        #定义单个日期,input_day = "4"
        #用户定义多个日期,input_day = "4,5"
        input_day = "4"
        #定义单个小时,input_hour ="17"
        #定义多个小时,input_hour = "17,18,19"
        input_hour = "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23"
        #定义1分钟,input_minute ="17"
        #定义多分钟,input_minute = "17,18,19,20,21,22,,23"
        input_minute = "3,13,23,33,43,53"
        #定义单周日,input_weekday ="0"
        #定义多周日,input_weekday = "0,1,2,3,4,5,6"#周一至周日，对应数字(0-6)
        #注意！若果定义了周的模式，则年月日定义设置则无效
        #该变量不填写任何值，则代表该项不设置，例如:input_weekday = ""
        input_weekday = "0,1,2,3,4,5,6"
        input_second = "1"
        #获取系统当前的时间戳
        now_year = datetime.datetime.now().year
        now_month = datetime.datetime.now().month
        now_day = datetime.datetime.now().day
        now_hour = datetime.datetime.now().hour
        now_minute = datetime.datetime.now().minute
        now_second = datetime.datetime.now().second
        now_weekday = datetime.datetime.now().weekday()
        #但条件满足用户输入条件，则运行以下语句
        #使用10 in list[10,20,30],这样的逻辑判断来执行，也就是系统当前获取的时间数据在用户设定的范围内，则进行执行
        #如果每天都执行或者每小时固定时间执行，则在天和小时执行模块设置跳过检查，
        #定义用户输入的变量值
        #定义存储时间的列表
        list_year = []
        list_month = []
        list_day = []
        list_hour = []
        list_minute = []
        list_second = []
        list_weekday = []
        #对用户输入的时间值进行处理
        for i in input_year.split(","):
            list_year.append(int(i))
        for i in input_month.split(","):
            list_month.append(int(i))
        for i in input_day.split(","):
            list_day.append(int(i))
        for i in input_hour.split(","):
            list_hour.append(int(i))
        for i in input_minute.split(","):
            list_minute.append(int(i))
        for i in input_second.split(","):
            list_second.append(int(i))
        for i in input_weekday.split(","):
            list_weekday.append(int(i))
        #如果用户设置了按周执行，则代码直接按每周的天数来进行判断，而不会去判断年月日
        if len(list_weekday) > 0:
            if now_weekday in list_weekday:
                if now_hour in list_hour:
                    if now_minute in list_minute:
                        if now_second in list_second:
                            print "Run second Task:%s",now_second
                            print "Run main Task:Start:weekday"
                            AutoUpdateRun()
                            time.sleep(1)
                        else:
                            time.sleep(1)
                            continue
                    else:
                        continue
                else:
                    continue
            else:
                continue
        else:
            if now_year in list_year:
                if now_month in list_month:
                    if now_day in list_day:
                       if now_hour in list_hour:
                           if now_minute in list_minute:
                               if now_second in list_second:
                                   print "Run second Task:%s",now_second
                                   print "Run main Task:Start"
                                   AutoUpdateRun()
                                   time.sleep(1)
                               else:
                                   time.sleep(1)
                                   continue
                           else:
                               continue
                       else:
                           continue
                    else:
                        continue
                else:
                    continue
            else:
                continue
# RunSche()
AutoUpdateRun()