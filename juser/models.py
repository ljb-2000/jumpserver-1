# coding: utf-8

from django.db import models
from django.contrib.auth.models import AbstractUser

import time
# from jasset.models import Asset, AssetGroup

#新增CMDB主机分类显示访问用户组

class CMDB_Group(models.Model):
    GROUP_TYPE_CHOICES = (
    ('CM', u"公司级别组"),
    ('DM', u"部门级别组"),
    ('BM', u"业务级别组")
    )
    name = models.CharField(max_length=80)
    company_name_id = models.CharField(max_length=10, blank=True, null=True)
    company_name = models.CharField(max_length=80,  blank=True,null=True)
    department_name_id = models.CharField(max_length=10, blank=True, null=True)
    department_name = models.CharField(max_length=80, blank=True,null=True)
    business_name_id = models.CharField(max_length=10, blank=True, null=True)
    business_name = models.CharField(max_length=80, blank=True,null=True)
    group_type = models.CharField(max_length=2, choices=GROUP_TYPE_CHOICES, default='CM',verbose_name=u"组类型")
    comment = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return self.name

class UserGroup(models.Model):
    name = models.CharField(max_length=80, unique=True)
    comment = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return self.name


class User(AbstractUser):
    USER_ROLE_CHOICES = (
        ('SU', 'SuperUser'),
        ('GA', 'GroupAdmin'),
        ('CU', 'CommonUser'),
    )
    name = models.CharField(max_length=80)
    uuid = models.CharField(max_length=100)
    role = models.CharField(max_length=2, choices=USER_ROLE_CHOICES, default='CU')
    group = models.ManyToManyField(UserGroup)
    ssh_key_pwd = models.CharField(max_length=200)
    #新增CMDB主机分类访问控制:2016-06-01
    company_name_id = models.CharField(max_length=10, blank=True, null=True)
    company_name = models.CharField(max_length=80)
    group_asset = models.ManyToManyField(CMDB_Group)
    # is_active = models.BooleanField(default=True)
    # last_login = models.DateTimeField(null=True)
    # date_joined = models.DateTimeField(null=True)

    def __unicode__(self):
        return self.username


class AdminGroup(models.Model):
    """
    under the user control group
    用户可以管理的用户组，或组的管理员是该用户
    """

    user = models.ForeignKey(User)
    group = models.ForeignKey(UserGroup)

    def __unicode__(self):
        return '%s: %s' % (self.user.username, self.group.name)


class Document(models.Model):
    def upload_to(self, filename):
        return 'upload/'+str(self.user.id)+time.strftime('/%Y/%m/%d/', time.localtime())+filename

    docfile = models.FileField(upload_to=upload_to)
    user = models.ForeignKey(User)

