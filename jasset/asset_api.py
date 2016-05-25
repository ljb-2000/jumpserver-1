# coding: utf-8
from __future__ import division
import xlrd
import xlsxwriter
from django.db.models import AutoField
from jumpserver.api import *
from jasset.models import ASSET_STATUS, ASSET_TYPE, ASSET_ENV, IDC, AssetRecord,ASSET_SALT_STATUS,ASSET_SSHKEY_STATUS,CompanyName,DepartmentName,BusinessName,AssetRelation
from jperm.ansible_api import MyRunner
from jperm.perm_api import gen_resource
from jumpserver.templatetags.mytags import get_disk_info


def group_add_asset(group, asset_id=None, asset_ip=None):
    """
    资产组添加资产
    Asset group add a asset
    """
    if asset_id:
        asset = get_object(Asset, id=asset_id)
    else:
        asset = get_object(Asset, ip=asset_ip)

    if asset:
        group.asset_set.add(asset)


def db_add_group(**kwargs):
    """
    add a asset group in database
    数据库中添加资产
    """
    name = kwargs.get('name')
    group = get_object(AssetGroup, name=name)
    asset_id_list = kwargs.pop('asset_select')

    if not group:
        group = AssetGroup(**kwargs)
        group.save()
        for asset_id in asset_id_list:
            group_add_asset(group, asset_id)
#新增CI项：公司名称入库:2016-05-10
def company_add_asset(company, asset_id=None, asset_ip=None):
    """
    公司添加资产
    Asset Company add a asset
    """
    if asset_id:
        asset = get_object(Asset, id=asset_id)
    else:
        asset = get_object(Asset, ip=asset_ip)

    if asset:
        company.asset_set.add(asset)

def department_add_asset(department, asset_id=None, asset_ip=None):
    """
    部门添加资产
    Asset Department add a asset
    """
    if asset_id:
        asset = get_object(Asset, id=asset_id)
    else:
        asset = get_object(Asset, ip=asset_ip)

    if asset:
        department.asset_set.add(asset)

def business_add_asset(business, asset_id=None, asset_ip=None):
    """
    业务添加资产
    Asset Business add a asset
    """
    if asset_id:
        asset = get_object(Asset, id=asset_id)
    else:
        asset = get_object(Asset, ip=asset_ip)

    if asset:
        business.asset_set.add(asset)

def db_add_company_name(**kwargs):
    """
    add a asset company_name in database
    数据库中添加公司名称
    """
    # name = kwargs.get('name')
    company = CompanyName(**kwargs)
    company.save()
    # company = get_object(CompanyName, name=name)
    # asset_id_list = kwargs.pop('asset_select')
    #
    # if not company:
    #     company = CompanyName(**kwargs)
    #     company.save()
        # for asset_id in asset_id_list:
        #     company_add_asset(company, asset_id)
def get_new_company_name_id(**kwargs):
    """
    获取最新添加的公司名称和公司ID(与部门，业务共用查询函数)
    :param:该函数参数必须输入最新添加的公司名称，同时查询数据库中最大的ID字段，通过这2个参数
    查询获取最新的公司名称和ID
    :return:
    """
    name = kwargs.get('name')
    table =  kwargs.get('table')
    company_all = table.objects.filter(name=name)
    list_id = []
    for company_list in company_all:
        list_id.append(company_list.id)
    company_id = max(list_id)
    print "asset_api.py:company_name:%s:company_id:%s:",(name,company_id)
    return name,company_id

def db_add_company_name_to_AssetRelation(**kwargs):
    """
    :param 新增功能，添加公司名称到关系表中，以记录公司，部门，业务的关系:
    :param 2016-05-20-01:通过
    :return:
    """
    company = AssetRelation(**kwargs)
    company.save()

def db_add_department_name_to_AssetRelation(**kwargs):
    """
    :param 新增功能，添加部门名称到关系表中，以记录公司，部门，业务的关系:
    :param 2016-05-20-01:通过
    :return:
    """

    department_name = kwargs.get('department_name')
    department_name_id =  kwargs.get('department_name_id')
    company_id = kwargs.get('company_id')
    #查询AssetRelation中，是否有以公司id和公司名称存储的行，但是部门id,部门名称，业务id,业务名称字段都为空，如果有这样的行
    #则直接更新这行的记录，在后面添加部门id和部门名称
    company_name = CompanyName.objects.get(id=company_id)
    department_add_check = AssetRelation.objects.all().filter(company_name_id__exact=company_id).filter(company_name__exact=company_name)
    update_id_01 = None
    for department_list in department_add_check:
        if department_list.department_name_id == None and department_list.department_name == None and department_list.business_name_id == None and department_list.business_name == None:
            print "department_list.id",department_list.id
            update_id_01 = department_list.id
    if update_id_01 != None:
        department = AssetRelation.objects.filter(id=update_id_01).update(department_name_id=department_name_id,department_name=department_name)
    else:
        department  = AssetRelation(company_name_id=company_id,company_name=company_name,department_name_id=department_name_id,department_name=department_name)
        department.save()
    # company = AssetRelation(**kwargs)
    # company.save()

def db_add_business_name_to_AssetRelation(**kwargs):
    """
    :param 新增功能，添加业务名称到关系表中，以记录公司，部门，业务的关系:
    :param 2016-05-23-01:
    :return:
    """

    business_name = kwargs.get('business_name')
    business_name_id =  kwargs.get('business_name_id')
    company_id = kwargs.get('company_id')
    department_id = kwargs.get('department_id')
    #查询AssetRelation中，是否有以公司id和公司名称存储的行，但是业务id,业务名称字段都为空，如果有这样的行
    #则直接更新这行的记录，在后面添加业务id和业务名称
    company_name = CompanyName.objects.get(id=company_id)
    department_name = DepartmentName.objects.get(id=department_id)
    business_add_check = AssetRelation.objects.all().filter(company_name_id__exact=company_id).filter(department_name_id__exact=department_id)
    update_id_01 = None
    for business_list in business_add_check:
        if  business_list.business_name_id == None and business_list.business_name == None:
            update_id_01 = business_list.id
    if update_id_01 != None:
        business = AssetRelation.objects.filter(id=update_id_01).update(business_name_id=business_name_id,business_name=business_name)
    else:
        business  = AssetRelation(company_name_id=company_id,company_name=company_name,department_name_id=department_id,department_name=department_name,business_name_id=business_name_id,business_name=business_name)
        business.save()
    # company = AssetRelation(**kwargs)
    # company.save()

def db_add_department_name(**kwargs):
    """
    add a asset department_name in database
    数据库中添加部门名称
    """
    department = DepartmentName(**kwargs)
    department.save()
     # name = kwargs.get('name')
    # department = get_object(DepartmentName, name=name)
    # asset_id_list = kwargs.pop('asset_select')

    # if not department:
    #     department = DepartmentName(**kwargs)
    #     department.save()
    #     for asset_id in asset_id_list:
    #         department_add_asset(department, asset_id)

def db_add_business_name(**kwargs):
    """
    add a asset business_name in database
    数据库中添加业务名称
    """
    asset_id_list = kwargs.pop('asset_select')
    business = BusinessName(**kwargs)
    business.save()
    #这里通过当前数据库的记录行进行的关联，不需要其它的文件
    for asset_id in asset_id_list:
            business_add_asset(business, asset_id)
    # name = kwargs.get('name')
    # business = get_object(BusinessName, name=name)
    # asset_id_list = kwargs.pop('asset_select')
    #
    # if not business:
    #     business = BusinessName(**kwargs)
    #     business.save()
    #     for asset_id in asset_id_list:
    #         business_add_asset(business, asset_id)

def db_update_company(**kwargs):
    """
    update a asset company_name in database
    数据库中更新公司名称
    """
    company_id = kwargs.pop('id')
    # asset_id_list = kwargs.pop('asset_select')
    # company = get_object(CompanyName, id=company_id)

    # for asset_id in asset_id_list:
    #     company_add_asset(company, asset_id)

    CompanyName.objects.filter(id=company_id).update(**kwargs)

def db_update_AssetRelation_company(**kwargs):
    """
    update a AssetRelation company_name in database
    更新关系数据库表中的公司名称
    """
    company_id = kwargs.pop('company_name_id')
    # asset_id_list = kwargs.pop('asset_select')
    # company = get_object(CompanyName, id=company_id)

    # for asset_id in asset_id_list:
    #     company_add_asset(company, asset_id)

    AssetRelation.objects.filter(company_name_id=company_id).update(**kwargs)

def db_update_AssetRelation_department(**kwargs):
    """
    update a AssetRelation department in database
    更新关系数据库表中的部门名称
    """
    department_id = kwargs.pop('department_name_id')
    AssetRelation.objects.filter(department_name_id=department_id).update(**kwargs)

def db_update_AssetRelation_business(**kwargs):
    """
    update a AssetRelation department in database
    更新关系数据库表中的部门名称
    """
    business_id = kwargs.pop('business_name_id')
    AssetRelation.objects.filter(business_name_id=business_id).update(**kwargs)

def db_update_department(**kwargs):
    """
    update a asset department_name in database
    数据库中更新部门名称
    """
    department_id = kwargs.pop('id')
    asset_id_list = kwargs.pop('asset_select')
    department = get_object(DepartmentName, id=department_id)

    for asset_id in asset_id_list:
        department_add_asset(department, asset_id)

    DepartmentName.objects.filter(id=department_id).update(**kwargs)

def db_update_business(**kwargs):
    """
    update a asset business_name in database
    数据库中更新业务名称
    """
    business_id = kwargs.pop('id')
    asset_id_list = kwargs.pop('asset_select')
    business = get_object(BusinessName, id=business_id)

    for asset_id in asset_id_list:
        business_add_asset(business, asset_id)

    BusinessName.objects.filter(id=business_id).update(**kwargs)

def db_update_group(**kwargs):
    """
    add a asset group in database
    数据库中更新资产
    """
    group_id = kwargs.pop('id')
    asset_id_list = kwargs.pop('asset_select')
    group = get_object(AssetGroup, id=group_id)

    for asset_id in asset_id_list:
        group_add_asset(group, asset_id)

    AssetGroup.objects.filter(id=group_id).update(**kwargs)


def db_asset_add(**kwargs):
    """
    add asset to db
    添加主机时数据库操作函数
    """
    group_id_list = kwargs.pop('groups')
    asset = Asset(**kwargs)
    asset.save()

    group_select = []
    for group_id in group_id_list:
        group = AssetGroup.objects.filter(id=group_id)
        group_select.extend(group)
    asset.group = group_select


def db_asset_update(**kwargs):
    """ 修改主机时数据库操作函数 """
    asset_id = kwargs.pop('id')
    Asset.objects.filter(id=asset_id).update(**kwargs)


def sort_ip_list(ip_list):
    """ ip地址排序 """
    ip_list.sort(key=lambda s: map(int, s.split('.')))
    return ip_list


def get_tuple_name(asset_tuple, value):
    """"""
    for t in asset_tuple:
        if t[0] == value:
            return t[1]

    return ''


def get_tuple_diff(asset_tuple, field_name, value):
    """"""
    old_name = get_tuple_name(asset_tuple, int(value[0])) if value[0] else u''
    new_name = get_tuple_name(asset_tuple, int(value[1])) if value[1] else u''
    alert_info = [field_name, old_name, new_name]
    return alert_info


def asset_diff(before, after):
    """
    asset change before and after
    """
    alter_dic = {}
    before_dic, after_dic = before, dict(after.iterlists())
    for k, v in before_dic.items():
        print "before_dic.itmes:%s:%s" % (k,v)
        after_dic_values = after_dic.get(k, [])
        print "after_dic_values:",after_dic_values
        if k == 'group':
            after_dic_value = after_dic_values if len(after_dic_values) > 0 else u''
            uv = v if v is not None else u''
            print "group uv value is:",uv
            print "group after_dic_value:",after_dic_value
        #新增CI项:2016-05-06:start
        elif k == 'company_name':
            after_dic_value = after_dic_values if len(after_dic_values) > 0 else u''
            uv = v if v is not None else u''
            print "company_name uv value is:",uv
            print "company_name after_dic_value:",after_dic_value
        elif k == 'department_name':
            after_dic_value = after_dic_values if len(after_dic_values) > 0 else u''
            uv = v if v is not None else u''
            print "department_name uv value is:",uv
            print "department_name after_dic_value:",after_dic_value
        elif k == 'business_name':
            after_dic_value = after_dic_values if len(after_dic_values) > 0 else u''
            uv = v if v is not None else u''
            print "business_name uv value is:",uv
            print "business_name after_dic_value:",after_dic_value
        else:
            after_dic_value = after_dic_values[0] if len(after_dic_values) > 0 else u''
            uv = unicode(v) if v is not None else u''
            print "other uv value is:",uv
            print "other after_dic_value:",after_dic_value
        if uv != after_dic_value:
            alter_dic.update({k: [uv, after_dic_value]})

    for k, v in alter_dic.items():
        # if k == 'business_name':
        #     print "asset_api.py:type:alter_dic[business_name][0]:144:",type(alter_dic['business_name'][0])
        #     print "asset_api.py:type:alter_dic[business_name][1]:145:",type(alter_dic['business_name'][1])
        # if k == 'company_name':
        #     print "asset_api.py:type:alter_dic[company_name][0]:144:",type(alter_dic['company_name'][0])
        #     print "asset_api.py:type:alter_dic[company_name][1]:145:",type(alter_dic['company_name'][1])
        # if k == 'department_name':
        #     print "asset_api.py:type:alter_dic[department_name][0]:144:",type(alter_dic['department_name'][0])
        #     print "asset_api.py:type:alter_dic[department_name][1]:145:",type(alter_dic['department_name'][1])
        # if k == 'group':
        #     print "asset_api.py:type:alter_dic[group][0]:147:",type(alter_dic['group'][0])
        #     print "asset_api.py:type:alter_dic[group][1]:148:",type(alter_dic['group'][1])
        if v == [None, u'']:
            alter_dic.pop(k)
    return alter_dic


def asset_diff_one(before, after):
    print before.__dict__, after.__dict__
    fields = Asset._meta.get_all_field_names()
    for field in fields:
        print before.field, after.field


def db_asset_alert(asset, username, alert_dic):
    """
    asset alert info to db
    """
    alert_list = []
    asset_tuple_dic = {'status': ASSET_STATUS, 'env': ASSET_ENV, 'asset_type': ASSET_TYPE, 'ci001':ASSET_SALT_STATUS,'ci002':ASSET_SSHKEY_STATUS}
    for field, value in alert_dic.iteritems():
        field_name = Asset._meta.get_field_by_name(field)[0].verbose_name
        # print "asset_api.py:field:166:",field
        # print "asset_api.py:field:167:",type(field)
        # print "asset_api.py:field:168:",value[0]
        # print "asset_api.py:field:value[0]:169:",type(value[0])
        # print "asset_api.py:field:vaule[1]:170:",type(value[1])
        if field == 'idc':
            old = IDC.objects.filter(id=value[0]) if value[0] else u''
            new = IDC.objects.filter(id=value[1]) if value[1] else u''
            old_name = old[0].name if old else u''
            new_name = new[0].name if new else u''
            alert_info = [field_name, old_name, new_name]

        elif field in ['status', 'env', 'asset_type','ci001','ci002']:
            alert_info = get_tuple_diff(asset_tuple_dic.get(field), field_name, value)

        elif field == 'group':
            old, new = [], []
            for group_id in value[0]:
                group_name = AssetGroup.objects.get(id=int(group_id)).name
                old.append(group_name)
            for group_id in value[1]:
                group_name = AssetGroup.objects.get(id=int(group_id)).name
                new.append(group_name)
            if sorted(old) == sorted(new):
                continue
            else:
                alert_info = [field_name, ','.join(old), ','.join(new)]

        #新增CI项:2016-05-06
        elif field == 'company_name':
            old, new = [], []
            for companyname_id in value[0]:
                company_name = CompanyName.objects.get(id=int(companyname_id)).name
                old.append(company_name)
            for companyname_id in value[1]:
                company_name = CompanyName.objects.get(id=int(companyname_id)).name
                new.append(company_name)
            if sorted(old) == sorted(new):
                continue
            else:
                alert_info = [field_name, ','.join(old), ','.join(new)]
        elif field == 'department_name':
            old, new = [], []
            for departmentname_id in value[0]:
                department_name = DepartmentName.objects.get(id=int(departmentname_id)).name
                old.append(department_name)
            for departmentname_id in value[1]:
                department_name = DepartmentName.objects.get(id=int(departmentname_id)).name
                new.append(department_name)
            if sorted(old) == sorted(new):
                continue
            else:
                alert_info = [field_name, ','.join(old), ','.join(new)]

        elif field == 'business_name':
            old, new = [], []
            for businessname_id in value[0]:
                business_name = BusinessName.objects.get(id=int(businessname_id)).name
                old.append(business_name)
            for businessname_id in value[1]:
                business_name = BusinessName.objects.get(id=int(businessname_id)).name
                new.append(business_name)
            if sorted(old) == sorted(new):
                continue
            else:
                alert_info = [field_name, ','.join(old), ','.join(new)]

        elif field == 'use_default_auth':
            if unicode(value[0]) == 'True' and unicode(value[1]) == 'on' or \
                                    unicode(value[0]) == 'False' and unicode(value[1]) == '':
                continue
            else:
                name = asset.username
                alert_info = [field_name, u'默认', name] if unicode(value[0]) == 'True' else \
                    [field_name, name, u'默认']

        elif field in ['username', 'password']:
            continue

        elif field == 'is_active':
            if unicode(value[0]) == 'True' and unicode(value[1]) == '1' or \
                                    unicode(value[0]) == 'False' and unicode(value[1]) == '0':
                continue
            else:
                alert_info = [u'是否激活', u'激活', u'禁用'] if unicode(value[0]) == 'True' else \
                    [u'是否激活', u'禁用', u'激活']

        else:
            alert_info = [field_name, unicode(value[0]), unicode(value[1])]

        if 'alert_info' in dir():
            alert_list.append(alert_info)

    if alert_list:
        AssetRecord.objects.create(asset=asset, username=username, content=alert_list)


def write_excel(asset_all):
    data = []
    now = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')
    file_name = 'cmdb_excel_' + now + '.xlsx'
    workbook = xlsxwriter.Workbook('static/files/excels/%s' % file_name)
    worksheet = workbook.add_worksheet(u'CMDB数据')
    worksheet.set_first_sheet()
    worksheet.set_column('A:E', 15)
    worksheet.set_column('F:F', 40)
    worksheet.set_column('G:Z', 15)
    title = [u'主机名', u'IP', u'IDC', u'所属主机组', u'操作系统', u'CPU', u'内存(G)', u'硬盘(G)',
             u'机柜位置', u'MAC', u'远控IP', u'机器状态', u'备注']
    for asset in asset_all:
        group_list = []
        for p in asset.group.all():
            group_list.append(p.name)

        disk = get_disk_info(asset.disk)
        group_all = '/'.join(group_list)
        status = asset.get_status_display()
        idc_name = asset.idc.name if asset.idc else u''
        system_type = asset.system_type if asset.system_type else u''
        system_version = asset.system_version if asset.system_version else u''
        system_os = unicode(system_type) + unicode(system_version)

        alter_dic = [asset.hostname, asset.ip, idc_name, group_all, system_os, asset.cpu, asset.memory,
                     disk, asset.cabinet, asset.mac, asset.remote_ip, status, asset.comment]
        data.append(alter_dic)
    format = workbook.add_format()
    format.set_border(1)
    format.set_align('center')
    format.set_align('vcenter')
    format.set_text_wrap()

    format_title = workbook.add_format()
    format_title.set_border(1)
    format_title.set_bg_color('#cccccc')
    format_title.set_align('center')
    format_title.set_bold()

    format_ave = workbook.add_format()
    format_ave.set_border(1)
    format_ave.set_num_format('0.00')

    worksheet.write_row('A1', title, format_title)
    i = 2
    for alter_dic in data:
        location = 'A' + str(i)
        worksheet.write_row(location, alter_dic, format)
        i += 1

    workbook.close()
    ret = (True, file_name)
    return ret


def copy_model_instance(obj):
    initial = dict([(f.name, getattr(obj, f.name))
                    for f in obj._meta.fields
                    if not isinstance(f, AutoField) and \
                    not f in obj._meta.parents.values()])
    return obj.__class__(**initial)


def ansible_record(asset, ansible_dic, username):
    alert_dic = {}
    asset_dic = asset.__dict__
    for field, value in ansible_dic.items():
        old = asset_dic.get(field)
        new = ansible_dic.get(field)
        if unicode(old) != unicode(new):
            setattr(asset, field, value)
            asset.save()
            alert_dic[field] = [old, new]

    db_asset_alert(asset, username, alert_dic)


def excel_to_db(excel_file):
    """
    Asset add batch function
    """
    try:
        data = xlrd.open_workbook(filename=None, file_contents=excel_file.read())
    except Exception, e:
        return False
    else:
        table = data.sheets()[0]
        rows = table.nrows
        for row_num in range(1, rows):
            row = table.row_values(row_num)
            if row:
                group_instance = []
                company_name_instance = []
                department_name_instance = []
                business_name_instance = []
                ip, port, hostname, use_default_auth, username, password, group, ci001, ci002, company_name, department_name, business_name, email, mobile_phone_number, level = row
                if get_object(Asset, hostname=hostname):
                    continue
                use_default_auth = 1 if use_default_auth == u'默认' else 0
                password_encode = CRYPTOR.encrypt(password) if password else ''
                #新增CI:2016-05-09
                ci001 = 1 if ci001 == u'1' else 0
                ci002 = 1 if ci002 == u'1' else 0
                if hostname:
                    asset = Asset(ip=ip,
                                  port=port,
                                  hostname=hostname,
                                  use_default_auth=use_default_auth,
                                  username=username,
                                  password=password_encode,
                                  ci001=ci001,
                                  ci002=ci002,
                                  email=str(email),
                                  mobile_phone_number=str(mobile_phone_number),
                                  level=str(level)
                                  )
                    asset.save()
                    group_list = group.split('/')
                    for group_name in group_list:
                        group = get_object(AssetGroup, name=group_name)
                        if group:
                            group_instance.append(group)
                    if group_instance:
                        asset.group = group_instance
                    #新增CI:2016-05-09
                    company_name_list = company_name.split('/')
                    for company_name_01 in company_name_list:
                        company_name_02 = get_object(CompanyName,name=company_name_01)
                        if company_name_02:
                            company_name_instance.append(company_name_02)
                    department_name_list = department_name.split('/')
                    for department_name_list_01 in department_name_list:
                        department_name_list_02 = get_object(DepartmentName,name=department_name_list_01)
                        if department_name_list_02:
                            department_name_instance.append(department_name_list_02)
                    business_name_list = business_name.split('/')
                    for business_name_list_01 in business_name_list:
                        business_name_list_02 = get_object(DepartmentName,name=business_name_list_01)
                        if business_name_list_02:
                            business_name_instance.append(business_name_list_02)

                    asset.save()
        return True


def get_ansible_asset_info(asset_ip, setup_info):
    print setup_info, '***'
    disk_need = {}
    disk_all = setup_info.get("ansible_devices")
    if disk_all:
        for disk_name, disk_info in disk_all.iteritems():
            if disk_name.startswith('sd') or disk_name.startswith('hd') or disk_name.startswith('vd') or disk_name.startswith('xvd'):
                disk_size = disk_info.get("size", '')
                if 'M' in disk_size:
                    disk_format = round(float(disk_size[:-2]) / 1000, 0)
                elif 'T' in disk_size:
                    disk_format = round(float(disk_size[:-2]) * 1000, 0)
                else:
                    disk_format = float(disk_size[:-2])
                disk_need[disk_name] = disk_format
    all_ip = setup_info.get("ansible_all_ipv4_addresses")
    other_ip_list = all_ip.remove(asset_ip) if asset_ip in all_ip else []
    other_ip = ','.join(other_ip_list) if other_ip_list else ''
    # hostname = setup_info.get("ansible_hostname")
    # ip = setup_info.get("ansible_default_ipv4").get("address")
    mac = setup_info.get("ansible_default_ipv4").get("macaddress")
    brand = setup_info.get("ansible_product_name")
    cpu_type = setup_info.get("ansible_processor")[1]
    cpu_cores = setup_info.get("ansible_processor_vcpus")
    cpu = cpu_type + ' * ' + unicode(cpu_cores)
    memory = setup_info.get("ansible_memtotal_mb")
    try:
        memory_format = int(round((int(memory) / 1000), 0))
    except Exception:
        memory_format = memory
    disk = disk_need
    system_type = setup_info.get("ansible_distribution")
    system_version = setup_info.get("ansible_distribution_version")
    system_arch = setup_info.get("ansible_architecture")
    # asset_type = setup_info.get("ansible_system")
    sn = setup_info.get("ansible_product_serial")
    asset_info = [other_ip, mac, cpu, memory_format, disk, sn, system_type, system_version, brand, system_arch]
    return asset_info


def asset_ansible_update(obj_list, name=''):
    resource = gen_resource(obj_list)
    ansible_instance = MyRunner(resource)
    ansible_asset_info = ansible_instance.run(module_name='setup', pattern='*')
    logger.debug('获取硬件信息: %s' % ansible_asset_info)
    for asset in obj_list:
        try:
            setup_info = ansible_asset_info['contacted'][asset.hostname]['ansible_facts']
        except KeyError:
            continue
        else:
            asset_info = get_ansible_asset_info(asset.ip, setup_info)
            other_ip, mac, cpu, memory, disk, sn, system_type, system_version, brand, system_arch = asset_info
            asset_dic = {"other_ip": other_ip,
                         "mac": mac,
                         "cpu": cpu,
                         "memory": memory,
                         "disk": disk,
                         "sn": sn,
                         "system_type": system_type,
                         "system_version": system_version,
                         "system_arch": system_arch,
                         "brand": brand
                         }

            ansible_record(asset, asset_dic, name)


def asset_ansible_update_all():
    name = u'定时更新'
    asset_all = Asset.objects.all()
    asset_ansible_update(asset_all, name)

