# coding:utf-8

from django.db.models import Q,F
from jasset.asset_api import *
from jumpserver.api import *
from jumpserver.models import Setting
from jasset.forms import AssetForm, IdcForm
from jasset.models import Asset, IDC, AssetGroup, ASSET_TYPE, ASSET_STATUS,AutoUpdataCI_Record,AssetRecord,cmdb_01,AssetRelation,CompanyName,DepartmentName,BusinessName,CMDB_PermRule
from jperm.perm_api import get_group_asset_perm, get_group_user_perm
import json
from django.http import HttpResponse
#导入juser应用的用户表,控制CMDB主机访问
from juser.models import User

@require_role('admin')
def group_add(request):
    """
    Group add view
    添加资产组
    """
    header_title, path1, path2 = u'添加资产组', u'资产管理', u'添加资产组'
    asset_all = Asset.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '')
        asset_select = request.POST.getlist('asset_select', [])
        comment = request.POST.get('comment', '')

        try:
            if not name:
                emg = u'组名不能为空'
                raise ServerError(emg)

            asset_group_test = get_object(AssetGroup, name=name)
            if asset_group_test:
                emg = u"该组名 %s 已存在" % name
                raise ServerError(emg)

        except ServerError:
            pass

        else:
            db_add_group(name=name, comment=comment, asset_select=asset_select)
            smg = u"主机组 %s 添加成功" % name

    return my_render('jasset/group_add.html', locals(), request)


@require_role('admin')
def group_edit(request):
    """
    Group edit view
    编辑资产组
    """
    header_title, path1, path2 = u'编辑主机组', u'资产管理', u'编辑主机组'
    group_id = request.GET.get('id', '')
    group = get_object(AssetGroup, id=group_id)

    asset_all = Asset.objects.all()
    asset_select = Asset.objects.filter(group=group)
    asset_no_select = [a for a in asset_all if a not in asset_select]

    if request.method == 'POST':
        name = request.POST.get('name', '')
        asset_select = request.POST.getlist('asset_select', [])
        comment = request.POST.get('comment', '')

        try:
            if not name:
                emg = u'组名不能为空'
                raise ServerError(emg)

            if group.name != name:
                asset_group_test = get_object(AssetGroup, name=name)
                if asset_group_test:
                    emg = u"该组名 %s 已存在" % name
                    raise ServerError(emg)

        except ServerError:
            pass

        else:
            group.asset_set.clear()
            db_update_group(id=group_id, name=name, comment=comment, asset_select=asset_select)
            smg = u"主机组 %s 添加成功" % name

        return HttpResponseRedirect(reverse('asset_group_list'))

    return my_render('jasset/group_edit.html', locals(), request)


@require_role('admin')
def group_list(request):
    """
    list asset group
    列出资产组
    """
    header_title, path1, path2 = u'查看资产组', u'资产管理', u'查看资产组'
    keyword = request.GET.get('keyword', '')
    asset_group_list = AssetGroup.objects.all()
    group_id = request.GET.get('id')
    if group_id:
        asset_group_list = asset_group_list.filter(id=group_id)
    if keyword:
        asset_group_list = asset_group_list.filter(Q(name__contains=keyword) | Q(comment__contains=keyword))

    asset_group_list, p, asset_groups, page_range, current_page, show_first, show_end = pages(asset_group_list, request)
    return my_render('jasset/group_list.html', locals(), request)


@require_role('admin')
def group_del(request):
    """
    Group delete view
    删除主机组
    """
    group_ids = request.GET.get('id', '')
    group_id_list = group_ids.split(',')

    for group_id in group_id_list:
        AssetGroup.objects.filter(id=group_id).delete()

    # return HttpResponse(u'删除成功')
    return my_render('jasset/jasset_warn.html', locals(), request)


@require_role('admin')
def asset_add(request):
    """
    Asset add view
    添加资产
    """
    header_title, path1, path2 = u'添加资产', u'资产管理', u'添加资产'
    asset_group_all = AssetGroup.objects.all()
    af = AssetForm()
    default_setting = get_object(Setting, name='default')
    default_port = default_setting.field2 if default_setting else ''
    if request.method == 'POST':
        af_post = AssetForm(request.POST)
        ip = request.POST.get('ip', '')
        hostname = request.POST.get('hostname', '')
        is_active = True if request.POST.get('is_active') == '1' else False
        use_default_auth = request.POST.get('use_default_auth', '')
        try:
            if Asset.objects.filter(hostname=unicode(hostname)):
                error = u'该主机名 %s 已存在!' % hostname
                raise ServerError(error)

        except ServerError:
            pass
        else:
            if af_post.is_valid():
                asset_save = af_post.save(commit=False)
                if not use_default_auth:
                    password = request.POST.get('password', '')
                    password_encode = CRYPTOR.encrypt(password)
                    asset_save.password = password_encode
                if not ip:
                    asset_save.ip = hostname
                asset_save.is_active = True if is_active else False
                asset_save.save()
                af_post.save_m2m()

                msg = u'主机 %s 添加成功' % hostname
            else:
                esg = u'主机 %s 添加失败' % hostname

    return my_render('jasset/asset_add.html', locals(), request)


@require_role('admin')
def asset_add_batch(request):
    header_title, path1, path2 = u'添加资产', u'资产管理', u'批量添加'
    return my_render('jasset/asset_add_batch.html', locals(), request)


@require_role('admin')
def asset_del(request):
    """
    del a asset
    删除主机
    """
    asset_id = request.GET.get('id', '')
    print "180:asset_id:",asset_id
    if asset_id:
        Asset.objects.filter(id=asset_id).delete()

    if request.method == 'POST':
        asset_batch = request.GET.get('arg', '')
        asset_id_all = str(request.POST.get('asset_id_all', ''))

        if asset_batch:
            for asset_id in asset_id_all.split(','):
                asset = get_object(Asset, id=asset_id)
                asset.delete()

    return HttpResponse(u'删除成功')


@require_role(role='super')
def asset_edit(request):
    """
    edit a asset
    修改主机
    """
    header_title, path1, path2 = u'修改资产', u'资产管理', u'修改资产'
    print "access asset_edit page"
    asset_id = request.GET.get('id', '')
    username = request.user.username
    asset = get_object(Asset, id=asset_id)
    if asset:
        password_old = asset.password
    # asset_old = copy_model_instance(asset)
    af = AssetForm(instance=asset)
    if request.method == 'POST':
        af_post = AssetForm(request.POST, instance=asset)
        ip = request.POST.get('ip', '')
        hostname = request.POST.get('hostname', '')
        password = request.POST.get('password', '')
        is_active = True if request.POST.get('is_active') == '1' else False
        use_default_auth = request.POST.get('use_default_auth', '')
        print "asset have change"
        try:
            asset_test = get_object(Asset, hostname=hostname)
            if asset_test and asset_id != unicode(asset_test.id):
                emg = u'该主机名 %s 已存在!' % hostname
                raise ServerError(emg)
        except ServerError:
            pass
        else:
            if af_post.is_valid():
                af_save = af_post.save(commit=False)
                if use_default_auth:
                    af_save.username = ''
                    af_save.password = ''
                    # af_save.port = None
                else:
                    if password:
                        password_encode = CRYPTOR.encrypt(password)
                        af_save.password = password_encode
                    else:
                        af_save.password = password_old
                af_save.is_active = True if is_active else False
                af_save.save()
                af_post.save_m2m()
                # asset_new = get_object(Asset, id=asset_id)
                # asset_diff_one(asset_old, asset_new)
                # print "af_post.__dict__.get('initial'):",af_post.__dict__.get('initial')
                # print "request.POST:",request.POST
                info = asset_diff(af_post.__dict__.get('initial'), request.POST)
                # print "views:info var:246:",info
                #info = {'group': [[1L], [u'1']], 'use_default_auth': [u'False', u''], 'is_active': [u'True', u'1'], 'department_name': [[1L], u'1'], 'company_name': [[1L], u'1'], 'business_name': [u'[1L]', u'1'], 'password': [u'3e61a17bcebe6ab3093cb86081210ee45d5fc11de52a4ba54550b2964d0342fd', u'']}
                db_asset_alert(asset, username, info)

                smg = u'主机 %s 修改成功' % ip
            else:
                emg = u'主机 %s 修改失败' % ip
                return my_render('jasset/error.html', locals(), request)
            return HttpResponseRedirect(reverse('asset_detail')+'?id=%s' % asset_id)

    return my_render('jasset/asset_edit.html', locals(), request)


@require_role('user')
def asset_list(request):
    """
    asset list view
    """
    header_title, path1, path2 = u'查看资产', u'资产管理', u'查看资产'
    username = request.user.username
    user_perm = request.session['role_id']
    idc_all = IDC.objects.filter()
    asset_group_all = AssetGroup.objects.all()
    asset_types = ASSET_TYPE
    asset_status = ASSET_STATUS
    idc_name = request.GET.get('idc', '')
    group_name = request.GET.get('group', '')
    asset_type = request.GET.get('asset_type', '')
    status = request.GET.get('status', '')
    keyword = request.GET.get('keyword', '')
    export = request.GET.get("export", False)
    group_id = request.GET.get("group_id", '')
    #新增CI项:start
    company_id = request.GET.get("company_id", '')
    department_id = request.GET.get("department_id", '')
    business_id = request.GET.get("business_id", '')
    company_name = request.GET.get("company_name",'')
    department_name = request.GET.get("department_name",'')
    business_name = request.GET.get("business_name",'')
    system_type = request.GET.get("system_type",'')
    env = request.GET.get("env",'')
    #新增CI项:End
    idc_id = request.GET.get("idc_id", '')
    asset_id_all = request.GET.getlist("id", '')
    company_all = CompanyName.objects.all()
    asset_env = ASSET_ENV

    if group_id:
        group = get_object(AssetGroup, id=group_id)
        if group:
            asset_find = Asset.objects.filter(group=group)
    #新增CI项:start
    elif company_id:
        company = get_object(CompanyName, id=company_id)
        if company:
            #清除上次查询的服务器例表
            asset_find = None
            #查询关系表，查看这个公司下面包含的部门，通过部门查询下面的业务名称，最后通过业务名称查询对应的服务器数量
            business =  AssetRelation.objects.all().filter(company_name_id__exact=company_id)
            businesst_id_list = []
            for business_list in business:
                businesst_id_list.append(business_list.business_name_id)
            #通过业务ID查询对应的服务器ID
            asset_id_list = []
            for index in range(len(businesst_id_list)):
                business_01 = BusinessName.objects.filter(id=businesst_id_list[index])
                for business_list in business_01:
                    for asset in business_list.asset_set.all():
                        asset_id_list.append(asset.id)
            #通过服务器的id,查询服务列表
            asset_find = Asset.objects.filter(pk__in=asset_id_list)
            #通过公司的id,过滤部门的ID信息
            department =  AssetRelation.objects.all().filter(company_name_id__exact=company_id)
            #根据公司id,获取部门ID
            department_id_list = []
            for department_list in department:
                department_id_list.append(department_list.department_name_id)
            #部门ID去重，根据部门ID查询对应的部门信息
            department_select = DepartmentName.objects.filter(pk__in=department_id_list)
            if department_id:
                # deparment = get_object(DepartmentName, id=department_id)
                # if deparment:
                #查询关系表，查看这个公司下面包含的部门，通过部门查询下面的业务名称，最后通过业务名称查询对应的服务器数量
                business =  AssetRelation.objects.all().filter(department_name_id__exact=department_id)
                businesst_id_list = []
                for business_list in business:
                    businesst_id_list.append(business_list.business_name_id)
                #通过业务ID查询对应的服务器ID
                asset_id_list = []
                for index in range(len(businesst_id_list)):
                    business_01 = BusinessName.objects.filter(id=businesst_id_list[index])
                    for business_list in business_01:
                        for asset in business_list.asset_set.all():
                            asset_id_list.append(asset.id)
                #通过服务器的id,查询服务列表
                asset_find = Asset.objects.filter(pk__in=asset_id_list)
                #根据部门ID，获取业务的ID
                business_select =  BusinessName.objects.filter(pk__in=businesst_id_list)
                if business_id:
                    business = get_object(BusinessName, id=business_id)
                    if business:
                        asset_find = Asset.objects.filter(business_name=business)
    # elif department_id:
    #     deparment = get_object(DepartmentName, id=department_id)
    #     if deparment:
    #         #查询关系表，查看这个公司下面包含的部门，通过部门查询下面的业务名称，最后通过业务名称查询对应的服务器数量
    #         business =  AssetRelation.objects.all().filter(department_name_id__exact=department_id)
    #         businesst_id_list = []
    #         for business_list in business:
    #             businesst_id_list.append(business_list.business_name_id)
    #         #通过业务ID查询对应的服务器ID
    #         asset_id_list = []
    #         for index in range(len(businesst_id_list)):
    #             business_01 = BusinessName.objects.filter(id=businesst_id_list[index])
    #             for business_list in business_01:
    #                 for asset in business_list.asset_set.all():
    #                     asset_id_list.append(asset.id)
    #         #通过服务器的id,查询服务列表
    #         asset_find = Asset.objects.filter(pk__in=asset_id_list)

    elif business_id:
        business = get_object(BusinessName, id=business_id)
        if business:
            asset_find = Asset.objects.filter(business_name=business)
    #新增CI项:End
    elif idc_id:
        idc = get_object(IDC, id=idc_id)
        if idc:
            asset_find = Asset.objects.filter(idc=idc)
    else:
        if user_perm != 0:
            asset_find = Asset.objects.all()
        else:
            asset_id_all = []
            user = get_object(User, username=username)
            asset_perm = get_group_user_perm(user) if user else {'asset': ''}
            user_asset_perm = asset_perm['asset'].keys()
            for asset in user_asset_perm:
                asset_id_all.append(asset.id)
            asset_find = Asset.objects.filter(pk__in=asset_id_all)
            asset_group_all = list(asset_perm['asset_group'])

    if idc_name:
        asset_find = asset_find.filter(idc__name__contains=idc_name)

    if group_name:
        asset_find = asset_find.filter(group__name__contains=group_name)

    if asset_type:
        asset_find = asset_find.filter(asset_type__contains=asset_type)

    if status:
        asset_find = asset_find.filter(status__contains=status)
    #新增根据操作系统类型过滤服务器列表
    if system_type:
        asset_find = asset_find.filter(system_type__contains=system_type)
    if env:
        asset_find = asset_find.filter(env__contains=env)
    if keyword:
        asset_find = asset_find.filter(
            Q(hostname__contains=keyword) |
            Q(other_ip__contains=keyword) |
            Q(ip__contains=keyword) |
            Q(remote_ip__contains=keyword) |
            Q(comment__contains=keyword) |
            Q(username__contains=keyword) |
            Q(group__name__contains=keyword) |
            Q(cpu__contains=keyword) |
            Q(memory__contains=keyword) |
            Q(disk__contains=keyword) |
            Q(brand__contains=keyword) |
            Q(cabinet__contains=keyword) |
            Q(sn__contains=keyword) |
            Q(system_type__contains=keyword) |
            Q(system_version__contains=keyword))
    if export:
        if asset_id_all:
            asset_find = []
            for asset_id in asset_id_all:
                asset = get_object(Asset, id=asset_id)
                if asset:
                    asset_find.append(asset)
        s = write_excel(asset_find)
        if s[0]:
            file_name = s[1]
        smg = u'excel文件已生成，请点击下载!'
        return my_render('jasset/asset_excel_download.html', locals(), request)
    search_num = asset_find.count()
    assets_list, p, assets, page_range, current_page, show_first, show_end = pages(asset_find, request)
    #新增操作系统列表显示
    system_type_list = []
    for asset_list in assets:
        system_type_list.append(asset_list.system_type)
    system_type_set = set(system_type_list)
    if user_perm != 0:
        return my_render('jasset/asset_list.html', locals(), request)
    else:
        return my_render('jasset/asset_cu_list.html', locals(), request)


@require_role('admin')
def asset_edit_batch(request):
    af = AssetForm()
    name = request.user.username
    asset_group_all = AssetGroup.objects.all()
    asset_business_all = BusinessName.objects.all()
    if request.method == 'POST':
        env = request.POST.get('env', '')
        idc_id = request.POST.get('idc', '')
        port = request.POST.get('port', '')
        use_default_auth = request.POST.get('use_default_auth', '')
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        group = request.POST.getlist('group', [])
        cabinet = request.POST.get('cabinet', '')
        comment = request.POST.get('comment', '')
        asset_id_all = unicode(request.GET.get('asset_id_all', ''))
        asset_id_all = asset_id_all.split(',')
        #新增批量修改业务名称功能:2016-05-27
        business = request.POST.getlist('business', [])
        for asset_id in asset_id_all:
            alert_list = []
            asset = get_object(Asset, id=asset_id)
            if asset:
                if env:
                    if asset.env != env:
                        asset.env = env
                        alert_list.append([u'运行环境', asset.env, env])
                if idc_id:
                    idc = get_object(IDC, id=idc_id)
                    name_old = asset.idc.name if asset.idc else u''
                    if idc and idc.name != name_old:
                        asset.idc = idc
                        alert_list.append([u'机房', name_old, idc.name])
                if port:
                    if unicode(asset.port) != port:
                        asset.port = port
                        alert_list.append([u'端口号', asset.port, port])

                if use_default_auth:
                    if use_default_auth == 'default':
                        asset.use_default_auth = 1
                        asset.username = ''
                        asset.password = ''
                        alert_list.append([u'使用默认管理账号', asset.use_default_auth, u'默认'])
                    elif use_default_auth == 'user_passwd':
                        asset.use_default_auth = 0
                        asset.username = username
                        password_encode = CRYPTOR.encrypt(password)
                        asset.password = password_encode
                        alert_list.append([u'使用默认管理账号', asset.use_default_auth, username])
                if group:
                    group_new, group_old, group_new_name, group_old_name = [], asset.group.all(), [], []
                    for group_id in group:
                        g = get_object(AssetGroup, id=group_id)
                        if g:
                            group_new.append(g)
                    if not set(group_new) < set(group_old):
                        group_instance = list(set(group_new) | set(group_old))
                        for g in group_instance:
                            group_new_name.append(g.name)
                        for g in group_old:
                            group_old_name.append(g.name)
                        asset.group = group_instance
                        alert_list.append([u'主机组', ','.join(group_old_name), ','.join(group_new_name)])
                #新增批量修改业务名称功能:2016-05-27
                if business:
                    business_new, business_old, business_new_name, business_old_name = [], asset.business_name.all(), [], []
                    for business_id in business:
                        business_obj = get_object(BusinessName, id=business_id)
                        if business_obj:
                            business_new.append(business_obj)
                    if not set(business_new) < set(business_old):
                        business_instance = list(set(business_new) | set(business_old))
                        for b in business_instance:
                            business_new_name.append(b.name)
                        for b in business_old:
                            business_old_name.append(b.name)
                        asset.business_name = business_instance
                        alert_list.append([u'业务名称', ','.join(business_old_name), ','.join(business_new_name)])
                if cabinet:
                    if asset.cabinet != cabinet:
                        asset.cabinet = cabinet
                        alert_list.append([u'机柜号', asset.cabinet, cabinet])
                if comment:
                    if asset.comment != comment:
                        asset.comment = comment
                        alert_list.append([u'备注', asset.comment, comment])
                asset.save()

            if alert_list:
                recode_name = unicode(name) + ' - ' + u'批量'
                AssetRecord.objects.create(asset=asset, username=recode_name, content=alert_list)
        return my_render('jasset/asset_update_status.html', locals(), request)

    return my_render('jasset/asset_edit_batch.html', locals(), request)


@require_role('admin')
def asset_detail(request):
    """
    Asset detail view
    """
    header_title, path1, path2 = u'主机详细信息', u'资产管理', u'主机详情'
    asset_id = request.GET.get('id', '')
    asset = get_object(Asset, id=asset_id)
    perm_info = get_group_asset_perm(asset)
    log = Log.objects.filter(host=asset.hostname)
    if perm_info:
        user_perm = []
        for perm, value in perm_info.items():
            if perm == 'user':
                for user, role_dic in value.items():
                    user_perm.append([user, role_dic.get('role', '')])
            elif perm == 'user_group' or perm == 'rule':
                user_group_perm = value
    print perm_info
    asset_record = AssetRecord.objects.filter(asset=asset).order_by('-alert_time')
    #获取公司名称和部门名称:2016-05-25
    #通过资产id查询到对应的业务名称ID,然后通过业务ID查询到对应的部门和公司名称
    business_id = None;department_name = None;company_name = None
    for object in asset.business_name.all():
        business_id = object.id
    if business_id:
        asset_object = get_object(AssetRelation, business_name_id=business_id)
        department_name = asset_object.department_name
        company_name = asset_object.company_name

    return my_render('jasset/asset_detail.html', locals(), request)


@require_role('admin')
def asset_update(request):
    """
    Asset update host info via ansible view
    """
    asset_id = request.GET.get('id', '')
    asset = get_object(Asset, id=asset_id)
    name = request.user.username
    if not asset:
        return HttpResponseRedirect(reverse('asset_detail')+'?id=%s' % asset_id)
    else:
        asset_ansible_update([asset], name)
    return HttpResponseRedirect(reverse('asset_detail')+'?id=%s' % asset_id)


@require_role('admin')
def asset_update_batch(request):
    if request.method == 'POST':
        arg = request.GET.get('arg', '')
        name = unicode(request.user.username) + ' - ' + u'自动更新'
        if arg == 'all':
            asset_list = Asset.objects.all()
        else:
            asset_list = []
            asset_id_all = unicode(request.POST.get('asset_id_all', ''))
            asset_id_all = asset_id_all.split(',')
            for asset_id in asset_id_all:
                asset = get_object(Asset, id=asset_id)
                if asset:
                    asset_list.append(asset)
        asset_ansible_update(asset_list, name)
        return HttpResponse(u'批量更新成功!')
    return HttpResponse(u'批量更新成功!')


@require_role('admin')
def idc_add(request):
    """
    IDC add view
    """
    header_title, path1, path2 = u'添加IDC', u'资产管理', u'添加IDC'
    if request.method == 'POST':
        idc_form = IdcForm(request.POST)
        if idc_form.is_valid():
            idc_name = idc_form.cleaned_data['name']

            if IDC.objects.filter(name=idc_name):
                emg = u'添加失败, 此IDC %s 已存在!' % idc_name
                return my_render('jasset/idc_add.html', locals(), request)
            else:
                idc_form.save()
                smg = u'IDC: %s添加成功' % idc_name
            return HttpResponseRedirect(reverse('idc_list'))
    else:
        idc_form = IdcForm()
    return my_render('jasset/idc_add.html', locals(), request)


@require_role('admin')
def idc_list(request):
    """
    IDC list view
    """
    header_title, path1, path2 = u'查看IDC', u'资产管理', u'查看IDC'
    posts = IDC.objects.all()
    keyword = request.GET.get('keyword', '')
    if keyword:
        posts = IDC.objects.filter(Q(name__contains=keyword) | Q(comment__contains=keyword))
    else:
        posts = IDC.objects.exclude(name='ALL').order_by('id')
    contact_list, p, contacts, page_range, current_page, show_first, show_end = pages(posts, request)
    return my_render('jasset/idc_list.html', locals(), request)


@require_role('admin')
def idc_edit(request):
    """
    IDC edit view
    """
    header_title, path1, path2 = u'编辑IDC', u'资产管理', u'编辑IDC'
    idc_id = request.GET.get('id', '')
    idc = get_object(IDC, id=idc_id)
    if request.method == 'POST':
        idc_form = IdcForm(request.POST, instance=idc)
        if idc_form.is_valid():
            idc_form.save()
            return HttpResponseRedirect(reverse('idc_list'))
    else:
        idc_form = IdcForm(instance=idc)
        return my_render('jasset/idc_edit.html', locals(), request)


@require_role('admin')
def idc_del(request):
    """
    IDC delete view
    """
    idc_ids = request.GET.get('id', '')
    idc_id_list = idc_ids.split(',')

    for idc_id in idc_id_list:
        IDC.objects.filter(id=idc_id).delete()

    return HttpResponseRedirect(reverse('idc_list'))


@require_role('admin')
def asset_upload(request):
    """
    Upload asset excel file view
    """
    if request.method == 'POST':
        excel_file = request.FILES.get('file_name', '')
        ret = excel_to_db(excel_file)
        if ret:
            smg = u'批量添加成功'
        else:
            emg = u'批量添加失败,请检查格式.'
    return my_render('jasset/asset_add_batch.html', locals(), request)

@require_role('user')
def tree_list(request):
    """
    asset list view
    """
    username = request.user.username
    user_perm = request.session['role_id']

    if user_perm != 0:
        return my_render('jasset/tree_list_03.html', locals(), request)
    else:
        return my_render('jasset/asset_cu_list.html', locals(), request)

@require_role('user')
def tree_list_02(request):
    """
    asset list view
    """
    username = request.user.username
    user_perm = request.session['role_id']

    if user_perm != 0:
        return my_render('jasset/tree_list_02.html', locals(), request)
    else:
        return my_render('jasset/asset_cu_list.html', locals(), request)

@require_role('user')
def tree_list_03(request):
    """
    asset list view
    """
    username = request.user.username
    user_perm = request.session['role_id']
    data_01 = json.dumps(AssetRelationGenerationNet());
    print "jasset.views.py:data_01;636:",data_01
    if user_perm != 0:
        return my_render('jasset/tree_list_04.html', locals(), request)
    else:
        return my_render('jasset/asset_cu_list.html', locals(), request)

@require_role('admin')
def company_add(request):
    """
    Company add view
    添加公司
    """
    header_title, path1, path2 = u'添加公司名称', u'公司名称管理', u'添加公司名称'
    asset_all = Asset.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '')
        # asset_select = request.POST.getlist('asset_select', [])
        comment = request.POST.get('comment', '')

        try:
            if not name:
                emg = u'公司名称不能为空'
                raise ServerError(emg)

            company_name_test = get_object(CompanyName, name=name)
            if company_name_test:
                emg = u"该公司名称 %s 已存在" % name
                raise ServerError(emg)

        except ServerError:
            pass

        else:
            db_add_company_name(name=name, comment=comment)
            #新增功能：记录公司名称到关系表中:2016-05-20
            company_name,company_name_id = get_new_company_name_id(name=name,table=CompanyName)
            db_add_company_name_to_AssetRelation(company_name=company_name,company_name_id=company_name_id)
            smg = u"公司名称 %s 添加成功" % name

    return my_render('jasset/company_name_add.html', locals(), request)


@require_role('admin')
def company_edit(request):
    """
    Group edit view
    编辑资产组
    """
    header_title, path1, path2 = u'编辑公司名称', u'资产管理', u'编辑公司名称'
    company_id = request.GET.get('id', '')
    company_name = get_object(CompanyName, id=company_id)

    # asset_all = Asset.objects.all()
    # asset_select = Asset.objects.filter(company_name=company_name)
    # asset_no_select = [a for a in asset_all if a not in asset_select]

    if request.method == 'POST':
        name = request.POST.get('name', '')
        # asset_select = request.POST.getlist('asset_select', [])
        comment = request.POST.get('comment', '')

        try:
            if not name:
                emg = u'公司名不能为空'
                raise ServerError(emg)

            if company_name.name != name:
                asset_group_test = get_object(CompanyName, name=name)
                if asset_group_test:
                    emg = u"该公司名 %s 已存在" % name
                    raise ServerError(emg)

        except ServerError:
            pass

        else:
            # company_name.asset_set.clear()
            db_update_company(id=company_id, name=name, comment=comment)
            #更新关系表中的公司名称
            db_update_AssetRelation_company(company_name_id=company_id,company_name=name)
            smg = u"公司名称 %s 添加成功" % name

        return HttpResponseRedirect(reverse('asset_company_list'))

    return my_render('jasset/company_name_edit.html', locals(), request)


@require_role('admin')
def company_list(request):
    """
    list Company name
    列出公司名称
    """
    header_title, path1, path2 = u'查看公司名称', u'资产管理', u'查看公司名称'
    keyword = request.GET.get('keyword', '')
    company_name_list = CompanyName.objects.all()
    company_id = request.GET.get('id')
    if company_id:
        company_name_list = company_name_list.filter(id=company_id)
    if keyword:
        company_name_list = company_name_list.filter(Q(name__contains=keyword) | Q(comment__contains=keyword))

    company_name_list, p, asset_companys, page_range, current_page, show_first, show_end = pages(company_name_list, request)
    return my_render('jasset/company_name_list.html', locals(), request)

@require_role('admin')
def company_del(request):
    """
    Company delete view
    删除公司名称
    """
    company_ids = request.GET.get('id', '')
    company_id_list = company_ids.split(',')

    for company_id in  company_id_list:
        #如果公司下面有部门，则先删除部门，然后再进行公司删除
        department_num = CompanyName.objects.get(pk__exact=company_id).num
        if department_num:
                smg = 0
                return HttpResponse(smg)
        else:
            CompanyName.objects.filter(id=company_id).delete()
            smg = 1
    return HttpResponse(smg)

#增加部门名称维护页面操作:start
@require_role('admin')
def department_add(request):
    """
    department add view
    添加部门
    """
    header_title, path1, path2 = u'添加部门名称', u'部门名称管理', u'添加部门名称'
    asset_all = Asset.objects.all()
    company_all = CompanyName.objects.all()
    #获取用户的id,通过用户ID获取用户所属公司
    username = request.user.name
    user_id = request.user.id
    company_name = request.user.company_name
    #获取CMDB规则表中权限类型ID为1,公司名称为公司1的规则行
    if username != 'admin':
       company_all = company_all.filter(name=company_name)
    #过滤公司名称，只显示本公司的部门信息

    if request.method == 'POST':
        name = request.POST.get('name', '')
        # asset_select = request.POST.getlist('asset_select', [])
        comment = request.POST.get('comment', '')
        #新增在公司节点添加部门名称功能:2016-05-20
        company_id = request.POST.get('company_id', '')

        try:
            if not name:
                emg = u'部门名称不能为空'
                raise ServerError(emg)
            if not company_id:
                emg = u'没有选择公司名称，请重新输入'
                raise ServerError(emg)

            #新增检查该公司名称是否在相同的公司已存在，若存在，则提示:需要传入公司的ID
            department_name_test = AssetRelation.objects.all().filter(company_name_id__exact=company_id).filter(department_name__exact=name)
            if department_name_test:
                emg = u"该部门名称 %s 已存在" % name
                raise ServerError(emg)
            #新增在公司名称下面新建部门，故部门名字可能会重复，所以去掉这个注释
            #department_name_test = get_object(DepartmentName, name=name)
            # if department_name_test:
            #     emg = u"该部门名称 %s 已存在" % name
            #     raise ServerError(emg)

        except ServerError:
            pass

        else:
            db_add_department_name(name=name, comment=comment)
            #新增功能：更新该部门对应的公司，记录公司下面有多少个部门,company_name表的num字段加1
            CompanyName.objects.filter(pk__exact=company_id).update(num=F('num')+1)
            #新增功能：记录部门名称到关系表中:2016-05-20
            department_name,department_name_id = get_new_company_name_id(name=name,table=DepartmentName)
            db_add_department_name_to_AssetRelation(department_name=department_name,department_name_id=department_name_id,company_id=company_id)
            smg = u"部门名称 %s 添加成功" % name

    return my_render('jasset/department_name_add.html', locals(), request)


@require_role('admin')
def department_edit(request):
    """
    department edit view
    编辑资产组
    """
    header_title, path1, path2 = u'编辑部门名称', u'资产管理', u'编辑部门名称'
    department_id = request.GET.get('id', '')
    department_name = get_object(DepartmentName, id=department_id)

    if request.method == 'POST':
        name = request.POST.get('name', '')
        asset_select = request.POST.getlist('asset_select', [])
        comment = request.POST.get('comment', '')

        try:
            if not name:
                emg = u'部门名不能为空'
                raise ServerError(emg)

            if department_name.name != name:
                asset_group_test = get_object(DepartmentName, name=name)
                if asset_group_test:
                    emg = u"该部门名 %s 已存在" % name
                    raise ServerError(emg)

        except ServerError:
            pass

        else:

            db_update_department(id=department_id, name=name, comment=comment, asset_select=asset_select)
            #更新关系表中的部门名称
            db_update_AssetRelation_department(department_name_id=department_id,department_name=name)
            smg = u"公司名称 %s 添加成功" % name

        return HttpResponseRedirect(reverse('asset_department_list'))

    return my_render('jasset/department_name_edit.html', locals(), request)


@require_role('admin')
def department_list(request):
    """
    list Department name
    列出部门名称
    """
    header_title, path1, path2 = u'查看部门名称', u'资产管理', u'查看部门名称'
    keyword = request.GET.get('keyword', '')
    company_id = request.GET.get('company_id', '')
    department_name_list = DepartmentName.objects.all()
    department_id = request.GET.get('id')
    perm_rule_all = CMDB_PermRule.objects.all()
    #获取用户的id,通过用户ID获取用户所属公司
    username = request.user.name
    user_id = request.user.id
    #获取CMDB规则表中权限类型ID为1,公司名称为公司1的规则行
    company_name = request.user.company_name
    perm_rule_find = perm_rule_all.filter(role_type_id=1).filter(company_name=company_name)
    user_name_list = []
    group_name_list = []
    for perm_rule in perm_rule_find:
        user_name_list.append(perm_rule.user_name)
        group_name_list.append(perm_rule.group_name)

    if company_id:
        department =  AssetRelation.objects.all().filter(company_name_id__exact=company_id)
        department_id_list = []
        for department_list in department:
            department_id_list.append(department_list.department_name_id)
        department_name_list = DepartmentName.objects.filter(pk__in=department_id_list)
    if department_id:
        department_name_list = department_name_list.filter(id=department_id)
    if keyword:
        department_name_list = department_name_list.filter(Q(name__contains=keyword) | Q(comment__contains=keyword))

    department_name_list, p, asset_departments, page_range, current_page, show_first, show_end = pages(department_name_list, request)
    return my_render('jasset/department_name_list.html', locals(), request)

@require_role('admin')
def department_del(request):
    """
    Department delete view
    删除部门名称
    """
    department_ids = request.GET.get('id', '')
    department_id_list = department_ids.split(',')

    for department_id in  department_id_list:
        #如果部门下面有业务，则先删除业务，然后再进行部门删除
        business_num = DepartmentName.objects.get(pk__exact=department_id).num
        if business_num:
            smg_flag = 0
            return HttpResponse(smg_flag)
        else:
            DepartmentName.objects.filter(id=department_id).delete()
            #部门名称删除，在公司表中更新num字段，代表这个公司下面少了一个部门
            object_company = AssetRelation.objects.filter(department_name_id__exact=department_id)[0:1].get()
            company_id = object_company.company_name_id
            CompanyName.objects.filter(pk__exact=company_id).update(num=F('num')-1)
            #删除关系表中的关系记录
            # AssetRelation.objects.filter(department_name_id=department_id).update(department_name_id=None,department_name=None)
            AssetRelation.objects.filter(department_name_id=department_id).delete()
            smg_flag = 1
    return HttpResponse(smg_flag)

#增加业务名称维护页面操作:start
@require_role('admin')
def business_add(request):
    """
    business add view
    添加业务名称
    """
    header_title, path1, path2 = u'添加业务名称', u'业务名称管理', u'添加业务名称'
    asset_all = Asset.objects.all()
    company_all = CompanyName.objects.all()
    #通过选择公司事件，过滤出对应的部门名称来
    company_id = request.GET.get('company_id', '')
    department_select = None
    smg = u'业务名称不能为空'
    if company_id:
        department = AssetRelation.objects.all().filter(company_name_id__exact=company_id)
        company_name = get_object(CompanyName, id=company_id)
        company_id = int(company_id)
        #根据公司id,获取部门ID
        department_id_list = []
        for department_list in department:
            department_id_list.append(department_list.department_name_id)
        #部门ID去重，根据部门ID查询对应的部门信息
        department_select = DepartmentName.objects.filter(pk__in=department_id_list)

    if request.method == 'POST':
        name = request.POST.get('name', '')
        asset_select = request.POST.getlist('asset_select', [])
        comment = request.POST.get('comment', '')
        #新增在公司节点->部门节点下面添加业务名称功能:2016-05-23
        company_id = request.POST.get('company_id', '')
        department_id = request.POST.get('department_id', '')

        try:
            if not name:
                emg = u'业务名称不能为空'
                raise ServerError(emg)
            if not company_id:
                emg = u'没有选择公司名称，请重新输入'
                raise ServerError(emg)
            if not department_id:
                emg = u'没有选择部门名称，请重新输入'
                raise ServerError(emg)

            #从关系表中检查，对应公司，部门下面是否已经存在该业务名称
            business_name_test = AssetRelation.objects.all().filter(company_name_id__exact=company_id).filter(department_name_id__exact=department_id).filter(business_name__exact=name)
            if business_name_test:
                emg = u"该业务名称 %s 已存在" % name
                raise ServerError(emg)
            # business_name_test = get_object(BusinessName, name=name)
            # if business_name_test:
            #     emg = u"该业务名称 %s 已存在" % name
            #     raise ServerError(emg)

        except ServerError:
            pass

        else:
            #先保存业务名称，然后获取业务名称的名字和ID，把这两个信息先保存到关系表，然后再将业务ID与资产ID进行关联
            db_add_business_name(name=name, comment=comment, asset_select=asset_select)
            #业务名称删除，在部门表中更新num字段，代表这个部门下面增加一个业务
            DepartmentName.objects.filter(pk__exact=department_id).update(num=F('num')+1)
            business_name,business_name_id = get_new_company_name_id(name=name,table=BusinessName)
            db_add_business_name_to_AssetRelation(business_name=business_name,business_name_id=business_name_id,company_id=company_id,department_id=department_id)
            smg = u"业务名称 %s 添加成功" % name

    return my_render('jasset/business_name_add.html', locals(), request)



@require_role('admin')
def business_edit(request):
    """
    business edit view
    编辑业务名称
    """
    header_title, path1, path2 = u'编辑业务名称', u'资产管理', u'编辑业务名称'
    business_id = request.GET.get('id', '')
    business_name = get_object(BusinessName, id=business_id)

    asset_all = Asset.objects.all()
    asset_select = Asset.objects.filter(business_name=business_name)
    asset_no_select = [a for a in asset_all if a not in asset_select]

    if request.method == 'POST':
        name = request.POST.get('name', '')
        asset_select = request.POST.getlist('asset_select', [])
        comment = request.POST.get('comment', '')

        try:
            if not name:
                emg = u'业务名不能为空'
                raise ServerError(emg)

            if business_name.name != name:
                asset_group_test = get_object(BusinessName, name=name)
                if asset_group_test:
                    emg = u"该业务名 %s 已存在" % name
                    raise ServerError(emg)

        except ServerError:
            pass

        else:
            business_name.asset_set.clear()
            db_update_business(id=business_id, name=name, comment=comment, asset_select=asset_select)
            #更新关系表中的业务名称
            db_update_AssetRelation_business(business_name_id=business_id,business_name=name)
            smg = u"业务名称 %s 添加成功" % name

        return HttpResponseRedirect(reverse('asset_business_list'))

    return my_render('jasset/business_name_edit.html', locals(), request)



@require_role('admin')
def business_list(request):
    """
    list business name
    列出业务名称
    """
    header_title, path1, path2 = u'查看业务名称', u'资产管理', u'查看业务名称'
    keyword = request.GET.get('keyword', '')
    department_id = request.GET.get('department_id', '')
    business_name_list = BusinessName.objects.all()
    business_id = request.GET.get('id')
    if department_id:
        business =  AssetRelation.objects.all().filter(department_name_id__exact=department_id)
        business_id_list = []
        for business_list in business:
            business_id_list.append(business_list.business_name_id)
        business_name_list = BusinessName.objects.filter(pk__in=business_id_list)
    if business_id:
        business_name_list = business_name_list.filter(id=business_id)
    if keyword:
        business_name_list = business_name_list.filter(Q(name__contains=keyword) | Q(comment__contains=keyword))

    business_name_list, p, asset_businesses, page_range, current_page, show_first, show_end = pages(business_name_list, request)
    return my_render('jasset/business_name_list.html', locals(), request)

@require_role('admin')
def business_del(request):
    """
    business delete view
    删除业务名称
    """
    business_ids = request.GET.get('id', '')
    business_id_list = business_ids.split(',')
    for business_id in  business_id_list:
        #如果业务下面有关联服务器，则先将服务器从该业务部门移出，然后再进行名称删除
        asset_list = BusinessName.objects.get(id=business_id).asset_set.all()
        # print "jasset.views.py:asset_list:1138:",asset_list

        if asset_list:
                smg_flag = 0
                # print "jasset.views.py:asset_list:1142:",asset_list
                print u'删除失败'
                #data = json.dumps({"id":"0", "name": "公司1", "parent_id": "0", "depth": "1"})
                return HttpResponse(smg_flag)
        else:
            BusinessName.objects.filter(id=business_id).delete()
            #业务名称删除，在部门表中更新num字段，代表这个部门下面少了一个业务
            object_department = AssetRelation.objects.filter(business_name_id__exact=business_id)[0:1].get()
            department_id = object_department.department_name_id
            DepartmentName.objects.filter(pk__exact=department_id).update(num=F('num')-1)
            #删除关系表的关系
            AssetRelation.objects.filter(business_name_id=business_id).update(business_name_id=None,business_name=None)
            smg_flag = 1
    return HttpResponse(smg_flag)



def AssetRelationGenerationNet():
    """
    查询AssetRelationGen生成一个树结构节点的信息表
    :return:
    """
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
        #生成第2条记录的节点信息,公司节点的parent_id要为0,但node_id需要紧接上层的node_id或者不能与上层ID重复即可,可以以21数字开头
    for data_list in data:
        for key02,value02 in data_list.iteritems():
            print "key02 is:%s:value02 is:%s"%(key02,value02)

    return data
#2016-05-10:用于测试小牛资产:start
@require_role('admin')
def group_del_xiaoniu(request):
    pass

def group_add_xiaoniu(request):
    pass

def group_list_xiaoniu(request):
    pass

def group_edit_xiaoniu(request):
    pass
#2016-05-10:用于测试小牛资产:End