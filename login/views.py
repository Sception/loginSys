from django.shortcuts import render, redirect
from . import models, forms
from django.utils import timezone
import hashlib
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
# Create your views here.


def index(request):
    return render(request, "login/index.html")


def hash_code(s, salt='login'):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())
    return h.hexdigest()


def make_confirm_string(user):
    now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.username, now)
    # confirm_string = models.ConfirmString()
    # confirm_string.code = code
    # confirm_string.user = user
    # confirm_string.save()
    models.ConfirmString.objects.create(code=code, user=user,)
    return code


def send_email(email, code):
    subject = '来自zoujie博客的注册确认邮件'
    text_content = '''感谢注册，这里是zoujie的博客和教程站点，专注于Python和Django技术的分享！\
                       如果你看到这条消息，说明你的邮箱服务器不提供HTML链接功能，请联系管理员！'''

    html_content = '''
                       <p>感谢注册<a href="http://{}/confirm/?code={}" target=blank>zoujie的博客</a>，\
                       这里是邹杰的博客和教程站点，专注于Python和Django技术的分享！</p>
                       <p>请点击站点链接完成注册确认！</p>
                       <p>此链接有效期为{}天！</p>
                       '''.format('127.0.0.1:8000', code, settings.CONFIRM_DAYS)

    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def register(request):
    if request.session.get('is_login', None):
        # 登录状态不允许注册。你可以修改这条原则！
        return redirect("/index/")
    if request.method == 'POST':
        register_form = forms.RegisterForm(request.POST)
        msg = "请检查填写的内容!"
        if register_form.is_valid():
            # 获取注册表中填写的数据 cleaned_data
            username = register_form.cleaned_data['username']
            password = register_form.cleaned_data['password']
            confirm_password = register_form.cleaned_data['confirm_password']
            email = register_form.cleaned_data['email']
            sex = register_form.cleaned_data['sex']
            if password != confirm_password:
                msg = "两次密码输入不一致，请重新输入"
                return render(request, "login/register.html", locals())
            else:
                same_name = models.User.objects.filter(username=username)
                if same_name:
                    msg = "用户名已存在，请重新填写用户名"
                    return render(request, "login/register.html", locals())

                same_email = models.User.objects.filter(email=email)
                if same_email:
                    msg = "邮箱已存在，请重新填写邮箱"
                    return render(request, "login/register.html", locals())
            # 所有条件成立时  创建新用户
            new_user = models.User()
            new_user.username = username
            # 使用加密密码
            new_user.password = hash_code(password)
            new_user.email = email
            new_user.sex = sex
            new_user.save()
            # 制作确认码作为邮件code
            code = make_confirm_string(new_user)
            # 发送注册邮件
            send_email(email, code)

            return redirect('/login/')
    register_form = forms.RegisterForm()
    return render(request, "login/register.html", locals())


def login(request):
    if request.session.get('is_login', None):
        return redirect('/index/')
    if request.method == 'POST':
        # username = request.POST.get('username', None)
        # password = request.POST.get('password', None)
        login_form = forms.UserForm(request.POST)
        # print(username, password)
        msg = "所有字段必须填写!"
        # if username and password:
        if login_form.is_valid():
            # username = username.strip()
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            try:
                user = models.User.objects.get(username=username)
                if not user.has_confirmed:
                    msg = "该用户还未通过邮件确认！"
                    return render(request, 'login/login.html', locals())
                if user.password == hash_code(password):
                    request.session['is_login'] = True
                    request.session['user_id'] = user.id
                    request.session['username'] = username
                    return redirect("/index/")
                else:
                    msg = "登录失败,密码不正确"
            except:
                msg = '用户名未找到'
        # return render(request, "login/login.html", {"msg": msg})
        print(locals())
        return render(request, "login/login.html", locals())
    login_form = forms.UserForm()
    return render(request, "login/login.html", locals())


def loginout(request):
    if not request.session.get('is_login', None):
        return redirect('/index/')
    request.session.flush()
    return redirect("/index/")


def user_confirm(request):
    code = request.GET.get('code', None)
    msg = ''
    try:
        confirm = models.ConfirmString.objects.get(code=code)
    except:
        msg = "无效的确认请求!"
        return render(request, "login/confirm.html", locals())

    create_time = confirm.create_time
    now = timezone.now()

    if now > create_time + timezone.timedelta(settings.CONFIRM_DAYS):
        confirm.user.delete()
        msg = "您的邮件已过期!请重新注册！"
        return render(request, "login/confirm.html", locals())
    else:
        confirm.user.has_confirmed = True
        confirm.user.save()
        # confirm.delete()
        msg = '感谢确认，请使用账户登录！'
        return render(request, 'login/confirm.html', locals())