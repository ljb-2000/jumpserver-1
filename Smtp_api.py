#!/usr/bin/python
#encoding:utf8
# 导入 smtplib 和 MIMEText
import smtplib
from email.mime.text import MIMEText
#定义发送列表
mailto_list=["342304628@qq.com"]
# 设置服务器名称、用户名、密码以及邮件后缀
mail_host = "smtp.xiaoniu66.com:25"
mail_user = "ouyangbin@xiaoniu66.com"
mail_pass = "oyb,p@ssw0rd"
mail_postfix="xiaoniu66.com"

# 发送邮件函数
def send_mail(to_list, sub):
    me = mail_user + "<"+mail_user+"@"+mail_postfix+">"
    fp = open('context.txt')
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

# if send_mail(mailto_list,"标题"):
#     print "测试成功"
# else:
#     print "测试失败"

#发送附件模块
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
title = 'check'
filename = 'file_check.html'
def send_mail_attach(to_list, sub, filename):
    me = mail_user + "<"+mail_user+"@"+mail_postfix+">"
    fp = open('context.txt')
    msg1 = MIMEText(fp.read(),_charset="utf-8")
    fp.close()
    msg = MIMEMultipart()
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    submsg = MIMEBase('application', 'x-xz')
    submsg.set_payload(open(filename,'rb').read())
    encoders.encode_base64(submsg)
    submsg.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(submsg)
    msg.attach(msg1)
    try:
        send_smtp = smtplib.SMTP()
        send_smtp.connect(mail_host)
        send_smtp.login(mail_user, mail_pass)
        send_smtp.sendmail(me, to_list, msg.as_string())
        send_smtp.close()
        return True
    except Exception, e:
        print str(e)[1]
        return False

if send_mail_attach(mailto_list,title,filename):
    print "发送成功"
else:
    print "发送失败"


