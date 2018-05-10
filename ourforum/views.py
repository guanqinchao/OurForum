# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404,render_to_response
from django.core.urlresolvers import reverse_lazy
from django.template import RequestContext
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldError
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
# from django.contrib import messages
from lbutils import get_client_ip
from django.views.generic import  DetailView,CreateView
from .templatetags.lbforum_filters import topic_can_post
from .forms import EditPostForm, NewPostForm, ForumForm
from .models import Topic, Forum, Post,Application,Notice
from ourforum.models import LoginUser as user
from ourforum.models import *
from ourforum_site.settings import base as settings
from django import http
from django.utils.http import is_safe_url
from django.utils.translation import (
    LANGUAGE_SESSION_KEY, check_for_language, get_language, to_locale,
)
User = user

def set_language(request):
    """
    Redirect to a given url while setting the chosen language in the session or cookie. The url and the language code need to be specified in the request parameters.
    Since this view changes how the user will see the rest of the site, it must only be accessed as a POST request. If called as a GET request, it will redirect to the page in the request (the 'next' parameter) without changing any state.

    当在 session 或 cookie 中设置所选择的语言时，会重定向到指定的网址。URL 和语言代码需要在 request 的参数中被指定。由于这个视图改变用户如何看到网站的其他部分，它必须只能通过 POST request. 如果调用 GET request, 它将重定向到 request 的那页，但没有任何状态改变。

    """
    next = request.POST.get('next', request.GET.get('next'))
    if not is_safe_url(url=next, host=request.get_host()):
        next = request.META.get('HTTP_REFERER')#using http://127.0.0.1:8000/  'HTTP_REFERER'
        if not is_safe_url(url=next, host=request.get_host()):
            next = '/'
    response = http.HttpResponseRedirect(next)#next is http://127.0.0.1:8000/
    if request.method == 'POST':
        lang_code = request.POST.get('language', None)
        if lang_code and check_for_language(lang_code):
            if hasattr(request, 'session'):
                request.session[LANGUAGE_SESSION_KEY] = lang_code;
                print(lang_code, 'session')#using this
            else:
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code,
                                    max_age=settings.LANGUAGE_COOKIE_AGE,
                                    path=settings.LANGUAGE_COOKIE_PATH,
                                    domain=settings.LANGUAGE_COOKIE_DOMAIN);print(lang_code, 'cookie')
    return response

def get_all_topics(user, select_related=True):
    topics = Topic.objects.all()
    if not (user.has_perm('ourforum.sft_mgr_forum')):
        qparam = Q(hidden=False)
        if user.is_authenticated:
            qparam = qparam | Q(forum__admins=user) | Q(posted_by=user)
        topics = topics.filter(qparam)
    if select_related:
        topics = topics.select_related(
            'posted_by__lbforum_profile',
            'last_post__last_updated_by__lbforum_profile',
            'forum'
        )
    return topics.distinct()


def get_all_posts(user, select_related=True):
    qs = Post.objects.all()
    if not (user.has_perm('ourforum.sft_mgr_forum')):
        qparam = Q(topic__hidden=False)
        if user.is_authenticated:
            qparam = qparam | Q(topic__forum__admins=user) | Q(posted_by=user)
        qs = qs.filter(qparam)
    if select_related:
        qs = qs.select_related(
            'posted_by', 'posted_by__lbforum_profile',
        )
    return qs.distinct()




def index(request, template_name="ourforum/index.html"):
    '''
        首页
        '''
    ctx = {}
    topics = None
    user = request.user
    topics = get_all_topics(user)
    topics = topics.order_by('-last_reply_on')[:20]
    ctx['topics'] = topics
    return render(request, template_name, ctx)


def recent(request, template_name="ourforum/recent.html"):
    ctx = {}
    user = request.user
    topics = get_all_topics(user)
    q = request.GET.get('q', '')
    if q:
        topics = topics.filter(subject__icontains=q)
    ctx['q'] = q
    ctx['topics'] = topics.order_by('-last_reply_on')
    ctx['request'] = request
    return render(request, template_name, ctx)


def forum(
        request, forum_slug, topic_type='', topic_type2='',
        template_name="ourforum/forum.html"):
    forum = get_object_or_404(Forum, slug=forum_slug)
    user = request.user
    topics = get_all_topics(user)
    topics = topics.filter(forum=forum)
    if topic_type and topic_type != 'good':
        topic_type2 = topic_type
        topic_type = ''
    if topic_type == 'good':
        topics = topics.filter(level__gt=30)
    if topic_type2:
        topics = topics.filter(topic_type__slug=topic_type2)

    order_by = request.GET.get('order_by', '-last_reply_on')

    try:
        topics = topics.order_by('-sticky', order_by)
    except FieldError:
        topics = topics.order_by('-sticky', '-last_reply_on')

    form = ForumForm(request.GET)
    ext_ctx = {
        'request': request,
        'form': form, 'forum': forum, 'topics': topics,
        'topic_type': topic_type, 'topic_type2': topic_type2}
    return render(request, template_name, ext_ctx)


def topic(request, topic_id, template_name="ourforum/topic.html"):
    user = request.user
    topic = get_object_or_404(Topic, pk=topic_id)
    if topic.hidden and not topic.forum.is_admin(user):
        return HttpResponse(ugettext('no right'))
    topic.num_views += 1
    topic.save()
    posts = get_all_posts(user)
    posts = posts.filter(topic=topic)
    posts = posts.filter(topic_post=False)
    posts = posts.order_by('created_on')
    ext_ctx = {
        'request': request,
        'topic': topic,
        'posts': posts,
        'has_replied': topic.has_replied(request.user),
        'can_admin': topic.forum.is_admin(user)
    }
    return render(request, template_name, ext_ctx)


def post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return HttpResponseRedirect(post.get_absolute_url_ext())


@csrf_exempt
def markitup_preview(request, template_name="ourforum/markitup_preview.html"):
    return render(request, template_name, {'message': request.POST['data']})


@login_required
def new_post(
        request, forum_id=None, topic_id=None, form_class=NewPostForm,
        template_name='ourforum/post.html'):
    user = request.user
    if not user.lbforum_profile.nickname:
        return redirect('lbforum_change_profile')
    qpost = topic = forum = first_post = preview = None
    post_type = _('topic')
    topic_post = True
    initial = {}
    if forum_id:
        forum = get_object_or_404(Forum, pk=forum_id)
    if topic_id:
        post_type = _('reply')
        topic_post = False
        topic = get_object_or_404(Topic, pk=topic_id)
        if not topic_can_post(topic, user):
            return HttpResponse(_("you can't reply, this topic closed."))
        forum = topic.forum
        first_post = topic.posts.order_by('created_on').first()
    initial['forum'] = forum
    if request.method == "POST":
        form = form_class(
            request.POST, user=user, forum=forum,
            initial=initial,
            topic=topic, ip=get_client_ip(request))
        preview = request.POST.get('preview', '')
        if form.is_valid() and request.POST.get('submit', ''):
            post = form.save()
            forum = post.topic.forum
            if topic:
                return HttpResponseRedirect(post.get_absolute_url_ext())
            else:
                return HttpResponseRedirect(reverse("lbforum_forum",
                                                    args=[forum.slug]))
    else:
        qid = request.GET.get('qid', '')
        if qid:
            qpost = get_object_or_404(Post, id=qid)
            initial['message'] = "[quote=%s]%s[/quote]" % (
                qpost.posted_by.lbforum_profile, qpost.message)
        form = form_class(initial=initial, forum=forum)
    ext_ctx = {
        'forum': forum,
        'show_forum_field': topic_post,
        'form': form,
        'topic': topic,
        'first_post': first_post,
        'post_type': post_type,
        'preview': preview
    }
    ext_ctx['attachments'] = user.lbattachment_set.filter(
        pk__in=request.POST.getlist('attachments'))
    ext_ctx['is_new_post'] = True
    ext_ctx['topic_post'] = topic_post
    return render(request, template_name, ext_ctx)


@login_required
def edit_post(request, post_id, form_class=EditPostForm,
              template_name="ourforum/post.html"):
    preview = None
    post_type = _('reply')
    edit_post = get_object_or_404(Post, id=post_id)
    if not (request.user.is_staff or request.user == edit_post.posted_by):
        return HttpResponse(ugettext('no right'))
    if edit_post.topic_post:
        post_type = _('topic')
    if request.method == "POST":
        form = form_class(instance=edit_post, user=request.user,
                          data=request.POST)
        preview = request.POST.get('preview', '')
        if form.is_valid() and request.POST.get('submit', ''):
            edit_post = form.save()
            return HttpResponseRedirect('../')
    else:
        form = form_class(instance=edit_post)
    ext_ctx = {
        'form': form,
        'post': edit_post,
        'topic': edit_post.topic,
        'forum': edit_post.topic.forum,
        'post_type': post_type,
        'preview': preview,
        'attachments': edit_post.attachments.all()
    }
    # ext_ctx['unpublished_attachments'] = request.user.lbattachment_set.filter(activated=False)
    ext_ctx['topic_post'] = edit_post.topic_post
    return render(request, template_name, ext_ctx)


@login_required
def delete_topic(request, topic_id):
    if not request.user.is_staff:
        # messages.error(_('no right'))
        return HttpResponse(ugettext('no right'))
    topic = get_object_or_404(Topic, id=topic_id)
    forum = topic.forum
    topic.delete()
    forum.update_state_info()
    return HttpResponseRedirect(reverse("lbforum_forum", args=[forum.slug]))


@login_required
def delete_post(request, post_id):
    if not request.user.is_staff:
        return HttpResponse(ugettext('no right'))
    post = get_object_or_404(Post, id=post_id)
    topic = post.topic
    post.delete()
    topic.update_state_info()
    topic.forum.update_state_info()
    # return HttpResponseRedirect(request.path)
    return HttpResponseRedirect(reverse("lbforum_topic", args=[topic.id]))


@login_required
def toggle_topic_attr(request, topic_id, attr):
    topic = get_object_or_404(Topic, id=topic_id)
    forum = topic.forum
    if not forum.is_admin(request.user):
        return HttpResponse(ugettext('no right'))
    if attr == 'sticky':
        topic.sticky = not topic.sticky
    elif attr == 'close':
        topic.closed = not topic.closed
    elif attr == 'hide':
        topic.hidden = not topic.hidden
    elif attr == 'distillate':
        topic.level = 30 if topic.level >= 60 else 60
    topic.save()
    return HttpResponseRedirect(reverse("lbforum_topic", args=[topic.id]))


# 加好友
def makefriend(request, sender, receiver):
    sender = User.objects.get(username=sender)
    receiver = User.objects.get(username=receiver)
    application = Application(sender=sender, receiver=receiver, status=0)
    application.save()
    return HttpResponse("OK申请发送成功！%s-->%s;<a href='/'>返回</a>" % (sender, receiver))

from django.template import context_processors
#消息通知
@login_required(login_url=reverse_lazy('user_login'))
def shownotice(request):
    notice_list = Notice.objects.filter(receiver=request.user,status=False)
    myfriends = LoginUser.objects.get(username=request.user).friends.all()
    c = context_processors.csrf(request)
    c.update({'notice_list':notice_list,'myfriends':myfriends})
    # return render_to_response('notice_list.html',{'notice_list':notice_list,'myfriends':myfriends},context_instance=RequestContext(request))
    return render_to_response('ourforum/notice_list.html', context=c)

# 具体通知
def noticedetail(request, pk):
    pk = int(pk)
    notice = Notice.objects.get(pk=pk)
    notice.status = True
    notice.save()
    if notice.type == 0:  # 评论通知
        post_id = notice.event.post.id
        return HttpResponseRedirect(reverse_lazy('post_detail', kwargs={"post_pk": post_id}))
    message_id = notice.event.id  # 消息通知
    return HttpResponseRedirect(reverse_lazy('message_detail', kwargs={"pk": message_id}))


# 好友同意/拒绝（flag 1同意，2拒绝）
def friendagree(request, pk, flag):
    flag = int(flag)
    pk = int(pk)
    entity = Notice.objects.get(pk=pk)
    entity.status = True
    application = entity.event
    application.status = flag

    application.receiver.friends.add(application.sender)
    application.save()
    entity.save()

    if flag == 1:
        str = "已加好友"
    else:
        str = "拒绝加好友"
    return HttpResponse(str)
from ourforum.forms import MessageForm
class MessageCreate(CreateView):
    model = Message
    template_name = 'ourforum/form.html'
    form_class = MessageForm
    #fields = ('content',)
    #SAE django1.5中fields失效，不知原因,故使用form_class
    success_url = reverse_lazy('show_notice')

    def form_valid(self, form):
        #此处有待加强安全验证
        sender = LoginUser.objects.get(username=self.request.user)
        receiver_id = int(self.kwargs.get('pk'))
        receiver = LoginUser.objects.get(id=receiver_id)
        formdata = form.cleaned_data
        formdata['sender'] = sender
        formdata['receiver'] = receiver
        m = Message(**formdata)
        m.save()
        return HttpResponse("消息发送成功！")

#具体消息
class MessageDetail(DetailView):
    model = Message
    template_name = "ourforum/message.html"
    context_object_name = 'message'


from PIL import (
    Image, ImageDraw, ImageFont, ImageFilter
)
#验证码
def verify_code(request):
    #引入随机函数模块
    import random
    #定义变量，用于画面的背景色、宽、高
    bgcolor = (random.randrange(20, 100), random.randrange(
        20, 100), 255)
    width = 100
    height = 50
    #创建画面对象
    im = Image.new('RGB', (width, height), bgcolor)
    #创建画笔对象
    draw = ImageDraw.Draw(im)
    #调用画笔的point()函数绘制噪点
    for i in range(0, 100):
        xy = (random.randrange(0, width), random.randrange(0, height))
        fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
        draw.point(xy, fill=fill)
    #定义验证码的备选值
    str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
    #随机选取4个值作为验证码
    rand_str = ''
    for i in range(0, 4):
        rand_str += str1[random.randrange(0, len(str1))]
    #构造字体对象，ubuntu的字体路径为“/usr/share/fonts/truetype/freefont”
    font = ImageFont.truetype('arial.ttf', 36)
    # font = ImageFont.load_default().font
    #构造字体颜色
    fontcolor = (255, random.randrange(0, 255), random.randrange(0, 255))
    #绘制4个字
    draw.text((5, 2), rand_str[0], font=font, fill=fontcolor)
    draw.text((25, 2), rand_str[1], font=font, fill=fontcolor)
    draw.text((50, 2), rand_str[2], font=font, fill=fontcolor)
    draw.text((75, 2), rand_str[3], font=font, fill=fontcolor)
    #释放画笔
    del draw
    #存入session，用于做进一步验证
    request.session['verifycode'] = rand_str
    """
    python2的为
    # 内存文件操作
    import cStringIO
    buf = cStringIO.StringIO()
    """
    # 内存文件操作-->此方法为python3的
    import io
    buf = io.BytesIO()
    #将图片保存在内存中，文件类型为png
    im.save(buf, 'png')
    #将内存中的图片数据返回给客户端，MIME类型为图片png
    return HttpResponse(buf.getvalue(), 'imge/png')

def verify_check2(request):
    """验证码的验证"""
    # 1.获取post请求当中的输入验证码的内容
    verify = request.POST.get('verify')
    # 2.获取浏览器请求当中的session中的值
    verifycode = request.session.get('verifycode')
    # 3.判断两个验证码是否相同
    if verify == verifycode:
        return HttpResponse('ok')
    else:
        return HttpResponse('err')

def show_verify2(request):
    """显示验证码界面"""
    return render(request, 'booktest/show_verify2.html')



def check_login(func):
    """
    验证登录状态装饰器
    :param func:
    :return:
    """

    def inner(request, *args, **kwargs):
        if request.session.get('loginuser'):
            return func(request, *args, **kwargs)
        else:
            return redirect('/login.html')

    return inner

import json
@check_login
def good(request, topic_id, user_id):
    """
    点赞
    :param request:
    :param article_id:
    :param user_id:
    :return:
    """
    result = {'status': True}
    new_read_count = int(
        Topic.objects.filter(id=topic_id).values('read_count').first().get('read_count')) - 1
    Topic.objects.filter(id=topic_id).update(read_count=str(new_read_count))
    if Up.objects.filter(topic_id=topic_id, user_id=user_id):
        result = {'status': False}
        return HttpResponse(json.dumps(result))
    else:
        Up.objects.create(up=False, topic_id=topic_id, user_id=user_id)
        new_up_count = int(Post.objects.filter(id=topic_id).values('up_count').first().get('up_count')) + 1
        Post.objects.filter(id=topic_id).update(up_count=str(new_up_count))
        Up.objects.filter(topic_id=topic_id, user_id=user_id).update(up=True)
        return HttpResponse(json.dumps(result))
