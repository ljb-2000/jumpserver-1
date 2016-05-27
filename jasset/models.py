# coding: utf-8
import datetime
from django.db import models
from juser.models import User, UserGroup

ASSET_ENV = (
    (1, U'生产环境'),
    (2, U'测试环境'),
    (3, U'开发环境'),
    )

ASSET_STATUS = (
    (1, u"已使用"),
    (2, u"未使用"),
    (3, u"报废")
    )

ASSET_TYPE = (
    (1, u"物理机"),
    (2, u"虚拟机"),
    (3, u"交换机"),
    (4, u"路由器"),
    (5, u"防火墙"),
    (6, u"Docker"),
    (7, u"其他")
    )
#新增自定义
ASSET_SALT_STATUS = (
    (0,u"否"),
    (1,u"是")
)
#新增自定义s
ASSET_SSHKEY_STATUS = (
    (0,u"否"),
    (1,u"是")
)

class AssetGroup(models.Model):
    GROUP_TYPE = (
        ('P', 'PRIVATE'),
        ('A', 'ASSET'),
    )
    name = models.CharField(max_length=80, unique=True)
    comment = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return self.name
#定义公司名称:新增自定义
class CompanyName(models.Model):
    name = models.CharField(max_length=80)
    num = models.IntegerField(default=0)
    comment = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return self.name
#定义部门名称：新增自定义
class DepartmentName(models.Model):
    name = models.CharField(max_length=80)
    num = models.IntegerField(default=0)
    comment = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return self.name
#定义业务名称:新增自定义
class BusinessName(models.Model):
    name = models.CharField(max_length=80)
    comment = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return self.name

class IDC(models.Model):
    name = models.CharField(max_length=32, verbose_name=u'机房名称')
    bandwidth = models.CharField(max_length=32, blank=True, null=True, default='', verbose_name=u'机房带宽')
    linkman = models.CharField(max_length=16, blank=True, null=True, default='', verbose_name=u'联系人')
    phone = models.CharField(max_length=32, blank=True, null=True, default='', verbose_name=u'联系电话')
    address = models.CharField(max_length=128, blank=True, null=True, default='', verbose_name=u"机房地址")
    network = models.TextField(blank=True, null=True, default='', verbose_name=u"IP地址段")
    date_added = models.DateField(auto_now=True, null=True)
    operator = models.CharField(max_length=32, blank=True, default='', null=True, verbose_name=u"运营商")
    comment = models.CharField(max_length=128, blank=True, default='', null=True, verbose_name=u"备注")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u"IDC机房"
        verbose_name_plural = verbose_name


class Asset(models.Model):
    """
    asset modle
    """
    ip = models.CharField(max_length=32, blank=True, null=True, verbose_name=u"主机IP")
    other_ip = models.CharField(max_length=255, blank=True, null=True, verbose_name=u"其他IP")
    hostname = models.CharField(unique=True, max_length=128, verbose_name=u"主机名")
    port = models.IntegerField(blank=True, null=True, verbose_name=u"端口号")
    group = models.ManyToManyField(AssetGroup, blank=True, verbose_name=u"所属主机组")
    username = models.CharField(max_length=16, blank=True, null=True, verbose_name=u"管理用户名")
    password = models.CharField(max_length=64, blank=True, null=True, verbose_name=u"密码")
    use_default_auth = models.BooleanField(default=True, verbose_name=u"使用默认管理账号")
    idc = models.ForeignKey(IDC, blank=True, null=True,  on_delete=models.SET_NULL, verbose_name=u'机房')
    mac = models.CharField(max_length=20, blank=True, null=True, verbose_name=u"MAC地址")
    remote_ip = models.CharField(max_length=16, blank=True, null=True, verbose_name=u'远控卡IP')
    brand = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'硬件厂商型号')
    cpu = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'CPU')
    memory = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'内存')
    disk = models.CharField(max_length=1024, blank=True, null=True, verbose_name=u'硬盘')
    system_type = models.CharField(max_length=32, blank=True, null=True, verbose_name=u"系统类型")
    system_version = models.CharField(max_length=8, blank=True, null=True, verbose_name=u"系统版本号")
    system_arch = models.CharField(max_length=16, blank=True, null=True, verbose_name=u"系统平台")
    cabinet = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'机柜号')
    position = models.IntegerField(blank=True, null=True, verbose_name=u'机器位置')
    number = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'资产编号')
    status = models.IntegerField(choices=ASSET_STATUS, blank=True, null=True, default=1, verbose_name=u"机器状态")
    asset_type = models.IntegerField(choices=ASSET_TYPE, blank=True, null=True, verbose_name=u"主机类型")
    env = models.IntegerField(choices=ASSET_ENV, blank=True, null=True, verbose_name=u"运行环境")
    sn = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"SN编号")
    date_added = models.DateTimeField(auto_now=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name=u"是否激活")
    comment = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"备注")
    # ci001字段为0,表示该主机没有安装salt-stack的agent；为1表示安装salt-stack的agent
    ci001 = models.IntegerField(choices=ASSET_SALT_STATUS, blank=True, null=True, verbose_name=u"是否安装salt")
    # ci002字段为0,表示该主机没有部署ssh-key文件；为1表示已部署ssh-key的文件
    ci002 = models.IntegerField(choices=ASSET_SSHKEY_STATUS, blank=True, null=True, verbose_name=u"是否部署ssh-key")
    #新增邮件地址
    email = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"邮件地址")
    #新增公司名称
    # company_name = models.ManyToManyField(CompanyName, blank=True, verbose_name=u"所属公司")
    #新增部门名称
    # department_name = models.ManyToManyField(DepartmentName, blank=True, verbose_name=u"所属部门")
    #新增电话号码
    mobile_phone_number = models.CharField(max_length=20,blank=True, null=True, verbose_name=u"移动电话")
    #新增业务故障响应级别
    level = models.CharField(max_length=2,blank=True, null=True, verbose_name=u"故障响应级别")
    #新增业务名称
    business_name = models.ManyToManyField(BusinessName, blank=True, verbose_name=u"业务名称")
    def __unicode__(self):
        return self.ip



class AssetRecord(models.Model):
    asset = models.ForeignKey(Asset)
    username = models.CharField(max_length=30, null=True)
    alert_time = models.DateTimeField(auto_now_add=True)
    content = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    job_id = models.CharField(max_length=20, null=True)
    main_task_id = models.CharField(max_length=20, null=True)
    email = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"邮件地址")



class AssetAlias(models.Model):
    user = models.ForeignKey(User)
    asset = models.ForeignKey(Asset)
    alias = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return self.alias

class AutoUpdataCI_Record(models.Model):
    hostname = models.CharField( max_length=128, null=True)
    username = models.CharField(max_length=30, null=True)
    alert_time = models.DateTimeField(auto_now_add=True)
    result = models.TextField(null=True, blank=True)
    job_id = models.CharField(max_length=20, null=True)
    comment = models.TextField(null=True, blank=True)
    email = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"邮件地址")
    main_task_id = models.CharField(max_length=20, null=True)
#新增的表结构，该表目前没有启用
class cmdb_01(models.Model):
    ip = models.CharField(max_length=32, blank=True, null=True, verbose_name=u"主机IP")
    hostname = models.CharField(unique=True, max_length=128, verbose_name=u"主机名")
    # ci001字段为0,表示该主机没有安装salt-stack的agent；为1表示安装salt-stack的agent
    ci001 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"属性1")
    # ci002字段为0,表示该主机没有部署ssh-key文件；为1表示已部署ssh-key的文件
    ci002 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"属性2")
    ci003 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"属性3")
    ci004 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"属性4")
    ci005 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"属性5")
    ci006 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"属性6")
    ci007 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"属性7")
    ci008 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"属性8")
    ci009 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"属性9")
    ci010 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"属性10")
    tag001 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"标签1")
    tag002 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"标签2")
    tag003 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"标签3")
    tag004 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"标签4")
    tag005 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"标签5")
    tag006 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"标签6")
    tag007 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"标签7")
    tag008 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"标签8")
    tag009 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"标签9")
    tag010 = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"标签10")

 #新增资产关系表，记录每个资产属于的公司，部门，业务信息
class AssetRelation(models.Model):
    num = models.CharField(max_length=10, blank=True, null=True, verbose_name=u'关系序号')
    company_name_id = models.CharField(max_length=10, blank=True, null=True)
    company_name = models.CharField(max_length=80,  blank=True,null=True)
    department_name_id = models.CharField(max_length=10, blank=True, null=True)
    department_name = models.CharField(max_length=80, blank=True,null=True)
    business_name_id = models.CharField(max_length=10, blank=True, null=True)
    business_name = models.CharField(max_length=80, blank=True,null=True)
    Relation_id = models.CharField(max_length=450, blank=True, null=True, verbose_name=u'关系id')
#新增资产关系表节点生成元素记录
class AssetRelationNet(models.Model):
    node_id = models.CharField(max_length=2, blank=True, null=True, verbose_name=u'树节点序号')
    name = models.CharField(max_length=450, blank=True, null=True, verbose_name=u'树节点名称')
    parent_id = models.CharField(max_length=2, blank=True, null=True, verbose_name=u'父节点序号')
    depth = models.CharField(max_length=2, blank=True, null=True, verbose_name=u'节点的层级')