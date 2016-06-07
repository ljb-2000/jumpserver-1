# coding: utf-8
# Author: Guanghongwei
# Email: ibuler@qq.com

# import random
# from Crypto.PublicKey import RSA
import uuid
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q
from juser.user_api import *
from jperm.perm_api import get_group_user_perm
from jasset.models import  CompanyName,DepartmentName,BusinessName,AssetRelation,CMDB_PermRule
from jumpserver.api import get_object


MAIL_FROM = EMAIL_HOST_USER


@require_role(role='super')
def group_add(request):
    """
    cmdb group add view for route
    添加CMDB用户组的视图
    """
    error = ''
    msg = ''
    header_title, path1, path2 = '添加用户组', '用户管理', '添加用户组'
    user_all = User.objects.all()
    #新增CMDB用户组添加:2016-06-02
    company_all = CompanyName.objects.all()
    department_all = DepartmentName.objects.all()
    business_all = BusinessName.objects.all()
    #获取对应的用户名,通过用户名获取对应的公司名称
    username = request.user.name
    user_id = request.user.id
    company_name = request.user.company_name
    company_id = request.user.company_name_id
    #获取该公司下面对应的部门
    if username == 'admin':
        company_id = request.GET.get("company_id", '')
    if company_id:
        department = AssetRelation.objects.all().filter(company_name_id__exact=company_id)
        #根据公司id,获取部门ID
        department_id_list = []
        for department_list in department:
            department_id_list.append(department_list.department_name_id)
        #部门ID去重，根据部门ID查询对应的部门信息
        department_select = DepartmentName.objects.filter(pk__in=department_id_list)
        #获取该用户对应的部门，业务列表
        group_id_list_for_departmanager,department_id_list_for_departmanager,business_id_list_for_departmanager = check_user_goups(user_id=user_id)
        if department_id_list_for_departmanager:
            department_select = department_select.filter(pk__in=department_id_list_for_departmanager)
    #从前端通过用户的部门选择事件，获取该部门的ID,通过部门ID，获取对应的业务ID列表
    department_id = request.GET.get("department_id", '')
    business_id = request.GET.get("business_id")
    group_type_tag = request.GET.get("group_type")
    #公司管理员权限控制,获取只能添加部门管理员，业务管理员类型的组
    #通过查询jasset_cmdb_permrule表，查询这3种管理员类型，查询该用户属于的公司，
    #根据公司ID，再通过查询perlrule表，过滤权限类型ID为1,2,3类型的ID，过滤关键字1为公司ID，过滤关键字2为权限类型ID
    #通过用户ID，查询用户属于公司级别的用户组，还是部门级别的用户组，还是业务级别的组
    #过滤条件1：公司ID，过滤对象:cmdb_group,获取该用户属于那些类型的组,是公司组或部门组或业务组
    role_type_list = cmdb_group_check(company_name_id=company_id,user_id=user_id)
    print "juser.views.py:role_type_list:61:",role_type_list
    user_name_list = []
    group_id_list = []
    acl_check = CMDB_PermRule.objects.filter(company_name_id__exact=company_id).filter(role_type_id__in=role_type_list)
    #通过以上条件过滤的行，在获取用名字段和用户组字段，再通过用户组字段获取这些用户组对应的用户名列表
    for acl_list in acl_check:
        user_name_list.append(acl_list.user_name)
        group_id_list.append(acl_list.group_id)
    print "juser.views.py:group_id_list:68:",group_id_list
    #去掉用户组的ID列中元素值为空的元素
    func1 = lambda x,y:x if y == '' else x + [y]
    group_id_list = reduce(func1, [[], ] + group_id_list)
    print "juser.views.py:group_id_list:71:",group_id_list
    for group_id in group_id_list:
        user_name_obj = get_object(CMDB_Group, id=int(group_id)).user_set.all()
        for list in user_name_obj:
            user_name_list.append(list.name)
    #去掉重复的用户名
    func = lambda x,y:x if y in x else x + [y]
    user_name_list = reduce(func, [[], ] + user_name_list)
    print "juser.views.py:user_name_list:79:",user_name_list
    print "juser.views.py:role_type_list:82:",role_type_list
    #根据用户的role_type_list来判断添加什么类型的用户组
    group_types = {}
    for role_type in role_type_list:
        if role_type == 1:
            group_types['DM'] = u"部门级别组"
        if role_type == 2:
            group_types['BM'] = u"业务级别组"
    if username == 'admin':
        group_types = {'CM': u"公司级别组",'DM': u"部门级别组", 'BM': u"业务级别组"}
    if department_id:
        business =  AssetRelation.objects.all().filter(department_name_id__exact=department_id)
        businesst_id_list = []
        for business_list in business:
            businesst_id_list.append(business_list.business_name_id)
        business_select = BusinessName.objects.filter(pk__in=businesst_id_list)

    if request.method == 'POST':
        group_name = request.POST.get('group_name', '')
        users_selected = request.POST.getlist('users_selected', '')
        comment = request.POST.get('comment', '')
        #新增资产类型组,
        group_type = request.POST.get('group_type', 'CM')
        #新增公司ID，部门ID，业务ID信息
        company_name_id  = request.POST.get('company_id', '')
        department_name_id = request.POST.get('department_id', '')
        business_name_id = request.POST.get('business_id', '')
        company_name = CompanyName.objects.get(id=int(company_name_id)).name
        department_name = ''
        business_name = ''
        if group_type == 'DM' or group_type == 'BM':
            department_name = DepartmentName.objects.get(id=int(department_name_id)).name
        if group_type == 'BM':
            business_name = BusinessName.objects.get(id=int(business_name_id)).name

        try:
            if not group_name:
                error = u'组名不能为空'
                raise ServerError(error)

            # if UserGroup.objects.filter(name=group_name):
            #     error = u'组名已存在'
            #     raise ServerError(error)
            db_add_cmdb_group(name=group_name, users_id=users_selected, comment=comment,group_type=group_type,company_name_id=company_name_id,company_name=company_name,department_name_id=department_name_id,department_name=department_name,business_name_id=business_name_id,business_name=business_name)
        except ServerError:
            pass
        except TypeError:
            error = u'添加小组失败'
        else:
            msg = u'添加组 %s 成功' % group_name

    return my_render('juser/group_add.html', locals(), request)


@require_role(role='super')
def group_list(request):
    """
    list user group
    用户组列表
    """
    header_title, path1, path2 = '查看用户组', '用户管理', '查看用户组'
    keyword = request.GET.get('search', '')
    user_group_list = CMDB_Group.objects.all().order_by('name')
    group_id = request.GET.get('id', '')
    #获取用户的id,通过用户ID获取用户所属公司
    username = request.user.name
    user_id = request.user.id
    company_name = request.user.company_name
    company_id = request.user.company_name_id
    #只显示本公司的用户组
    if username != 'admin':
        user_group_list = user_group_list.filter(company_name_id__exact=company_id)
    #根据用户ID，查询用户是否在公司管理员组，部门管理员组，业务管理员组，若在这3种类型的组中，则显示组的添加，删除，编辑按钮
    #根据公司ID，再通过查询perlrule表，过滤权限类型ID为1,2,3类型的ID，过滤关键字1为公司ID，过滤关键字2为权限类型ID
    role_type_list = cmdb_group_check(company_name_id=company_id,user_id=user_id)
    print "juser.views.py:role_type_list:149:",role_type_list
    user_name_list = []
    group_id_list = []
    acl_check = CMDB_PermRule.objects.filter(company_name_id__exact=company_id).filter(role_type_id__in=role_type_list)
    #通过以上条件过滤的行，在获取用名字段和用户组字段，再通过用户组字段获取这些用户组对应的用户名列表
    for acl_list in acl_check:
        user_name_list.append(acl_list.user_name)
        group_id_list.append(acl_list.group_id)
    print "juser.views.py:group_id_list:128:",group_id_list
    #去掉用户组的ID列中元素值为空的元素
    func1 = lambda x,y:x if y == '' else x + [y]
    group_id_list = reduce(func1, [[], ] + group_id_list)
    print "juser.views.py:group_id_list:131:",group_id_list
    for group_id_for_user in group_id_list:
        user_name_obj = get_object(CMDB_Group, id=int(group_id_for_user)).user_set.all()
        for list in user_name_obj:
            user_name_list.append(list.name)
    #去掉重复的用户名
    func = lambda x,y:x if y in x else x + [y]
    user_name_list = reduce(func, [[], ] + user_name_list)
    print "juser.views.py:user_name_list:136:",user_name_list
    #根据role_type_list显示的用户类型过滤用户组
    group_type_list = []
    for role_type in role_type_list:
        if role_type == 1:
            group_type_list.append('DM')
        if role_type == 2:
            group_type_list.append('BM')
    print "juser.views.py:group_type_list:180:",group_type_list
    print "juser.views.py:user_group_list:181:",user_group_list
    if username != 'admin':
        if group_type_list:
            user_group_list = user_group_list.filter(group_type__in=group_type_list)
            print "juser.views.py:user_group_list:185:",user_group_list
        #部门管理员角色，通过查询该用户属于那个部门来控制只显示本部门下面的业务管理员组,通过用户组属于不同的部门业务来控制权限
        group_id_list_for_departmanager,department_id_list_for_departmanager,business_id_list_for_departmanager = check_user_goups(user_id=user_id)
        print "juser.views.py:department_id_list_for_departmanager:186:",department_id_list_for_departmanager
        if department_id_list_for_departmanager:
            user_group_list = user_group_list.filter(department_name_id__in=department_id_list_for_departmanager)

    if keyword:
        user_group_list = user_group_list.filter(Q(name__icontains=keyword) | Q(comment__icontains=keyword))

    if group_id:
        user_group_list = user_group_list.filter(id=int(group_id))

    user_group_list, p, user_groups, page_range, current_page, show_first, show_end = pages(user_group_list, request)
    return my_render('juser/group_list.html', locals(), request)


@require_role(role='super')
def group_del(request):
    """
    del a group
    删除用户组
    """
    group_ids = request.GET.get('id', '')
    group_id_list = group_ids.split(',')
    for group_id in group_id_list:
        CMDB_Group.objects.filter(id=group_id).delete()

    return HttpResponse('删除成功')


@require_role(role='super')
def group_edit(request):
    error = ''
    msg = ''
    header_title, path1, path2 = '编辑用户组', '用户管理', '编辑用户组'

    if request.method == 'GET':
        group_id = request.GET.get('id', '')
        user_group = get_object(CMDB_Group, id=group_id)
        # user_group = UserGroup.objects.get(id=group_id)
        users_selected = User.objects.filter(group_asset=user_group)
        users_remain = User.objects.filter(~Q(group_asset=user_group))
        users_all = User.objects.all()

    elif request.method == 'POST':
        group_id = request.POST.get('group_id', '')
        group_name = request.POST.get('group_name', '')
        comment = request.POST.get('comment', '')
        users_selected = request.POST.getlist('users_selected')

        try:
            if '' in [group_id, group_name]:
                raise ServerError('组名不能为空')

            if len(CMDB_Group.objects.filter(name=group_name)) > 1:
                raise ServerError(u'%s 用户组已存在' % group_name)
            # add user group
            user_group = get_object_or_404(CMDB_Group, id=group_id)
            user_group.user_set.clear()

            for user in User.objects.filter(id__in=users_selected):
                user.group_asset.add(CMDB_Group.objects.get(id=group_id))

            user_group.name = group_name
            user_group.comment = comment
            user_group.save()
        except ServerError, e:
            error = e

        if not error:
            return HttpResponseRedirect(reverse('user_group_list'))
        else:
            users_all = User.objects.all()
            users_selected = User.objects.filter(group=user_group)
            users_remain = User.objects.filter(~Q(group=user_group))

    return my_render('juser/group_edit.html', locals(), request)


@require_role(role='super')
def user_add(request):
    error = ''
    msg = ''
    header_title, path1, path2 = '添加用户', '用户管理', '添加用户'
    user_role = {'SU': u'超级管理员', 'CU': u'普通用户', 'GA': u'组管理员'}
    group_all = CMDB_Group.objects.all()
    company_all = CompanyName.objects.all()
    #获取对应的用户名,通过用户名获取对应的公司名称
    username = request.user.name
    user_id = request.user.id
    company_name = request.user.company_name
    company_id = request.user.company_name_id
    #获取该公司下面对应的部门
    if username != 'admin':
        company_all = company_all.filter(id__exact=company_id)
    #根据用户是公司管理员，部门管理员,业务管理员获取对应的权限类型
    role_type_list = cmdb_group_check(company_name_id=company_id,user_id=user_id)
    #根据role_type_list显示的用户类型过滤用户组
    group_type_list = []
    for role_type in role_type_list:
        if role_type == 1:
            group_type_list.append('DM')
        if role_type == 2:
            group_type_list.append('BM')
    print "juser.views.py:group_type_list:177:",group_type_list
    if username != 'admin':
        if group_type_list:
            group_all = group_all.filter(group_type__in=group_type_list).filter(company_name_id__exact=company_id)
            #获取该用户对应的部门，业务列表
            group_id_list_for_departmanager,department_id_list_for_departmanager,business_id_list_for_departmanager = check_user_goups(user_id=user_id)
            if department_id_list_for_departmanager:
                group_all = group_all.filter(department_name_id__in=department_id_list_for_departmanager)
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = PyCrypt.gen_rand_pass(16)
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        groups = request.POST.getlist('groups', [])
        admin_groups = request.POST.getlist('admin_groups', [])
        role = request.POST.get('role', 'CU')
        uuid_r = uuid.uuid4().get_hex()
        ssh_key_pwd = PyCrypt.gen_rand_pass(16)
        extra = request.POST.getlist('extra', [])
        is_active = False if '0' in extra else True
        ssh_key_login_need = True
        send_mail_need = True if '2' in extra else False
        #新增公司名称属性:
        company_id = request.POST.get('company_id', '')
        company_name = get_object(CompanyName,id=company_id)


        try:
            if '' in [username, password, ssh_key_pwd, name, role]:
                error = u'带*内容不能为空'
                raise ServerError
            check_user_is_exist = User.objects.filter(username=username)
            if check_user_is_exist:
                error = u'用户 %s 已存在' % username
                raise ServerError

        except ServerError:
            pass
        else:
            try:
                user = db_add_user(username=username, name=name,
                                   password=password,
                                   email=email, role=role, uuid=uuid_r,
                                   groups=groups, admin_groups=admin_groups,
                                   ssh_key_pwd=ssh_key_pwd,
                                   is_active=is_active,
                                   date_joined=datetime.datetime.now(),company_name=company_name,company_name_id=company_id)
                server_add_user(username, password, ssh_key_pwd, ssh_key_login_need)
                user = get_object(User, username=username)
                if groups:
                    user_groups = []
                    for user_group_id in groups:
                        user_groups.extend(CMDB_Group.objects.filter(id=user_group_id))

            except IndexError, e:
                error = u'添加用户 %s 失败 %s ' % (username, e)
                try:
                    db_del_user(username)
                    server_del_user(username)
                except Exception:
                    pass
            else:
                if MAIL_ENABLE and send_mail_need:
                    user_add_mail(user, kwargs=locals())
                msg = get_display_msg(user, password, ssh_key_pwd, ssh_key_login_need, send_mail_need)
    return my_render('juser/user_add.html', locals(), request)


@require_role(role='super')
def user_list(request):
    user_role = {'SU': u'超级管理员', 'GA': u'组管理员', 'CU': u'普通用户'}
    header_title, path1, path2 = '查看用户', '用户管理', '用户列表'
    keyword = request.GET.get('keyword', '')
    gid = request.GET.get('gid', '')
    users_list = User.objects.all().order_by('username')

    if gid:
        user_group = CMDB_Group.objects.filter(id=gid)
        if user_group:
            user_group = user_group[0]
            users_list = user_group.user_set.all()

    if keyword:
        users_list = users_list.filter(Q(username__icontains=keyword) | Q(name__icontains=keyword)).order_by('username')

    users_list, p, users, page_range, current_page, show_first, show_end = pages(users_list, request)

    return my_render('juser/user_list.html', locals(), request)


@require_role(role='user')
def user_detail(request):
    header_title, path1, path2 = '用户详情', '用户管理', '用户详情'
    if request.session.get('role_id') == 0:
        user_id = request.user.id
    else:
        user_id = request.GET.get('id', '')

    user = get_object(User, id=user_id)
    if not user:
        return HttpResponseRedirect(reverse('user_list'))

    user_perm_info = get_group_user_perm(user)
    role_assets = user_perm_info.get('role')
    user_log_ten = Log.objects.filter(user=user.username).order_by('id')[0:10]
    user_log_last = Log.objects.filter(user=user.username).order_by('id')[0:50]
    user_log_last_num = len(user_log_last)

    return my_render('juser/user_detail.html', locals(), request)


@require_role(role='admin')
def user_del(request):
    if request.method == "GET":
        user_ids = request.GET.get('id', '')
        user_id_list = user_ids.split(',')
    elif request.method == "POST":
        user_ids = request.POST.get('id', '')
        user_id_list = user_ids.split(',')
    else:
        return HttpResponse('错误请求')

    for user_id in user_id_list:
        user = get_object(User, id=user_id)
        if user and user.username != 'admin':
            logger.debug(u"删除用户 %s " % user.username)
            bash('userdel -r %s' % user.username)
            user.delete()
    return HttpResponse('删除成功')


@require_role('admin')
def send_mail_retry(request):
    uuid_r = request.GET.get('uuid', '1')
    user = get_object(User, uuid=uuid_r)
    msg = u"""
    跳板机地址： %s
    用户名：%s
    重设密码：%s/juser/password/forget/
    请登录web点击个人信息页面重新生成ssh密钥
    """ % (URL, user.username, URL)

    try:
        send_mail(u'邮件重发', msg, MAIL_FROM, [user.email], fail_silently=False)
    except IndexError:
        return Http404
    return HttpResponse('发送成功')


@defend_attack
def forget_password(request):
    if request.method == 'POST':
        defend_attack(request)
        email = request.POST.get('email', '')
        username = request.POST.get('username', '')
        name = request.POST.get('name', '')
        user = get_object(User, username=username, email=email, name=name)
        if user:
            timestamp = int(time.time())
            hash_encode = PyCrypt.md5_crypt(str(user.uuid) + str(timestamp) + KEY)
            msg = u"""
            Hi %s, 请点击下面链接重设密码！
            %s/juser/password/reset/?uuid=%s&timestamp=%s&hash=%s
            """ % (user.name, URL, user.uuid, timestamp, hash_encode)
            send_mail('忘记跳板机密码', msg, MAIL_FROM, [email], fail_silently=False)
            msg = u'请登陆邮箱，点击邮件重设密码'
            return http_success(request, msg)
        else:
            error = u'用户不存在或邮件地址错误'

    return render_to_response('juser/forget_password.html', locals())


@defend_attack
def reset_password(request):
    uuid_r = request.GET.get('uuid', '')
    timestamp = request.GET.get('timestamp', '')
    hash_encode = request.GET.get('hash', '')
    action = '/juser/password/reset/?uuid=%s&timestamp=%s&hash=%s' % (uuid_r, timestamp, hash_encode)

    if hash_encode == PyCrypt.md5_crypt(uuid_r + timestamp + KEY):
        if int(time.time()) - int(timestamp) > 600:
            return http_error(request, u'链接已超时')
    else:
        return HttpResponse('hash校验失败')

    if request.method == 'POST':
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        print password, password_confirm
        if password != password_confirm:
            return HttpResponse('密码不匹配')
        else:
            user = get_object(User, uuid=uuid_r)
            if user:
                user.password = PyCrypt.md5_crypt(password)
                user.save()
                return http_success(request, u'密码重设成功')
            else:
                return HttpResponse('用户不存在')

    else:
        return render_to_response('juser/reset_password.html', locals())

    return http_error(request, u'错误请求')


@require_role(role='super')
def user_edit(request):
    header_title, path1, path2 = '编辑用户', '用户管理', '编辑用户'
    if request.method == 'GET':
        user_id = request.GET.get('id', '')
        if not user_id:
            return HttpResponseRedirect(reverse('index'))

        user_role = {'SU': u'超级管理员', 'CU': u'普通用户', 'GA': u'组管理员'}
        user = get_object(User, id=user_id)
        group_all = CMDB_Group.objects.all()
        company_name = user.company_name
        company_all = CompanyName.objects.all()
        if user:
            groups_str = ' '.join([str(group.id) for group in user.group_asset.all()])
            admin_groups_str = ' '.join([str(admin_group.group.id) for admin_group in user.admingroup_set.all()])

    else:
        user_id = request.GET.get('id', '')
        password = request.POST.get('password', '')
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        # groups = request.POST.getlist('groups', [])
        role_post = request.POST.get('role', 'CU')
        admin_groups = request.POST.getlist('admin_groups', [])
        extra = request.POST.getlist('extra', [])
        is_active = True if '0' in extra else False
        email_need = True if '2' in extra else False
        user_role = {'SU': u'超级管理员', 'GA': u'部门管理员', 'CU': u'普通用户'}
        if user_id:
            user = get_object(User, id=user_id)
        else:
            return HttpResponseRedirect(reverse('user_list'))

        if password != '':
            password_decode = password
        else:
            password_decode = None

        db_update_user(user_id=user_id,
                       password=password,
                       name=name,
                       email=email,
                       # groups=groups,
                       admin_groups=admin_groups,
                       role=role_post,
                       is_active=is_active)

        if email_need:
            msg = u"""
            Hi %s:
                您的信息已修改，请登录跳板机查看详细信息
                地址：%s
                用户名： %s
                密码：%s (如果密码为None代表密码为原密码)
                权限：：%s

            """ % (user.name, URL, user.username, password_decode, user_role.get(role_post, u''))
            send_mail('您的信息已修改', msg, MAIL_FROM, [email], fail_silently=False)

        return HttpResponseRedirect(reverse('user_list'))
    return my_render('juser/user_edit.html', locals(), request)


@require_role('user')
def profile(request):
    user_id = request.user.id
    if not user_id:
        return HttpResponseRedirect(reverse('index'))
    user = User.objects.get(id=user_id)
    return my_render('juser/profile.html', locals(), request)


def change_info(request):
    header_title, path1, path2 = '修改信息', '用户管理', '修改个人信息'
    user_id = request.user.id
    user = User.objects.get(id=user_id)
    error = ''
    if not user:
        return HttpResponseRedirect(reverse('index'))

    if request.method == 'POST':
        name = request.POST.get('name', '')
        password = request.POST.get('password', '')
        email = request.POST.get('email', '')

        if '' in [name, email]:
            error = '不能为空'

        if not error:
            User.objects.filter(id=user_id).update(name=name, email=email)
            if len(password) > 0:
                user.set_password(password)
                user.save()
            msg = '修改成功'

    return my_render('juser/change_info.html', locals(), request)


@require_role(role='user')
def regen_ssh_key(request):
    uuid_r = request.GET.get('uuid', '')
    user = get_object(User, uuid=uuid_r)
    if not user:
        return HttpResponse('没有该用户')

    username = user.username
    ssh_key_pass = PyCrypt.gen_rand_pass(16)
    gen_ssh_key(username, ssh_key_pass)
    return HttpResponse('ssh密钥已生成，密码为 %s, 请到下载页面下载' % ssh_key_pass)


@require_role(role='user')
def down_key(request):
    if is_role_request(request, 'super'):
        uuid_r = request.GET.get('uuid', '')
    else:
        uuid_r = request.user.uuid

    if uuid_r:
        user = get_object(User, uuid=uuid_r)
        if user:
            username = user.username
            private_key_file = os.path.join(KEY_DIR, 'user', username+'.pem')
            print private_key_file
            if os.path.isfile(private_key_file):
                f = open(private_key_file)
                data = f.read()
                f.close()
                response = HttpResponse(data, content_type='application/octet-stream')
                response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(private_key_file)
                return response
    return HttpResponse('No Key File. Contact Admin.')

