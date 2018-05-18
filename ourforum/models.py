# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _#国际化支持
# from django.conf import settings
from ourforum_site.settings  import base as settings
from easy_thumbnails.fields import ThumbnailerImageField
from easy_thumbnails.files import get_thumbnailer
from el_pagination import settings as elp_setttings
from django.utils.encoding import python_2_unicode_compatible

from lbattachment.models import LBAttachment
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
@python_2_unicode_compatible
class Category(models.Model):
    name = models.CharField(max_length=100)
    descn = models.TextField(blank=True)

    oid = models.PositiveIntegerField(default=999)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'category'
        verbose_name = _(u"Category")
        verbose_name_plural = _(u"Categories")
        ordering = ('-oid', 'created_on')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Forum(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110)
    description = models.TextField(default='')
    oid = models.PositiveIntegerField(default=999)
    category = models.ForeignKey(Category,verbose_name=u"Category")
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    num_topics = models.IntegerField(default=0)
    num_posts = models.IntegerField(default=0)

    last_post = models.ForeignKey(
        'Post', models.SET_NULL,
        verbose_name=_('Last post'),
        blank=True, null=True)

    class Meta:
        verbose_name = _(u"Forum")
        verbose_name_plural = _(u"Forums")
        ordering = ('oid', '-created_on')
        permissions = (
            ("sft_mgr_forum", _("Forum-Administrator")),
        )

    def __str__(self):
        return self.name

    def _count_nums_topic(self):
        return self.topic_set.all().count()

    def _count_nums_post(self):
        return Post.objects.filter(topic__forum=self).count()

    @models.permalink
    def get_absolute_url(self):
        return ('lbforum_forum', (), {'forum_slug': self.slug})

    def update_state_info(self, last_post=None, commit=True):
        self.num_topics = self._count_nums_topic()
        self.num_posts = self._count_nums_post()
        if not last_post:
            last_post = Post.objects.filter(
                topic__forum=self).order_by('-created_on').first()
        self.last_post = last_post
        if commit:
            self.save()

    def is_admin(self, user):
        if user.has_perm('ourforum.sft_mgr_forum'):
            return True
        return self.admins.filter(pk=user.pk).exists()


@python_2_unicode_compatible
class TopicType(models.Model):
    forum = models.ForeignKey(Forum, verbose_name=_(u'Forum'))
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    class Meta:
        verbose_name = _(u"TopicType")
        verbose_name_plural = _(u"TopicTypes")
    def __str__(self):
        return self.name

LEVEL_CHOICES = (
    (30, _('Default')),
    (60, _('Distillate')),
)


@python_2_unicode_compatible
class Topic(models.Model):
    forum = models.ForeignKey(Forum, verbose_name=_(u'Forum'))
    topic_type = models.ForeignKey(
        TopicType, verbose_name=_(u'TopicType'),
        blank=True, null=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL)

    post = models.ForeignKey(
        'Post', verbose_name=_('Post'),
        related_name='topics', blank=True, null=True)
    subject = models.CharField(max_length=999)

    num_views = models.IntegerField(default=0)
    num_replies = models.PositiveSmallIntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    last_reply_on = models.DateTimeField(auto_now_add=True)
    last_post = models.ForeignKey(
        'Post', models.SET_NULL,
        verbose_name=_('Last post'),
        related_name='last_post_topics', blank=True, null=True)

    has_imgs = models.BooleanField(default=False)
    has_attachments = models.BooleanField(default=False)
    need_replay = models.BooleanField(default=False)  # need_reply :-)
    need_reply_attachments = models.BooleanField(default=False)

    closed = models.BooleanField(default=False)
    sticky = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    level = models.SmallIntegerField(choices=LEVEL_CHOICES, default=30)

    class Meta:
        ordering = ('-last_reply_on',)  # '-sticky'
        get_latest_by = ('created_on')
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'

    def __str__(self):
        return self.subject

    def _count_nums_replies(self):
        return self.posts.filter(topic_post=False).count()

    @models.permalink
    def get_absolute_url(self):
        return ('lbforum_topic', (), {'topic_id': self.id})

    def has_replied(self, user):
        if user.is_anonymous():
            return False
        return Post.objects.filter(posted_by=user, topic=self).count()

    def update_state_info(self, last_post=None, commit=True):
        self.num_replies = self._count_nums_replies()
        if not last_post:
            last_post = self.posts.order_by('-created_on').first()
        self.last_post = last_post
        if commit:
            self.save()

class Up(models.Model):
    """
    记录赞表
    """

    post = models.ForeignKey(verbose_name='发言', to='Topic', to_field='id', on_delete=models.CASCADE)
    user = models.ForeignKey(verbose_name='赞用户', to='LoginUser', to_field='id', on_delete=models.CASCADE)
    up = models.BooleanField(verbose_name='是否赞')


@python_2_unicode_compatible
class Post(models.Model):
    FORMAT_CHOICES = (
        ('bbcode', _('BBCode')),
        ('markdown', _('Markdown')),
        ('html', _('Html')),
    )
    topic = models.ForeignKey(Topic, verbose_name=_(u'Topic'), related_name='posts')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    poster_ip = models.GenericIPAddressField()
    topic_post = models.BooleanField(default=False)
    comment_parent = models.ForeignKey('self', blank=True, null=True, related_name='childcomment')
    format = models.CharField(max_length=20, default='bbcode', choices=FORMAT_CHOICES)
    message = models.TextField()
    attachments = models.ManyToManyField(LBAttachment, blank=True)

    has_imgs = models.BooleanField(default=False)
    has_attachments = models.BooleanField(default=False)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='last_updated_by_posts',
        blank=True, null=True)

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")
        ordering = ('-created_on',)
        get_latest_by = ('created_on', )

    def __str__(self):
        return self.message[:80]

    def subject(self):
        if self.topic_post:
            return _('Topic: %s') % self.topic.subject
        return _('Re: %s') % self.topic.subject

    def file_attachments(self):
        return self.attachments.filter(is_img=False)

    def img_attachments(self):
        return self.attachments.filter(is_img=True)

    def _update_attachments_flag(self):
        self.has_attachments = self.attachments.filter(is_img=False).exists()
        self.has_imgs = self.attachments.filter(is_img=True).exists()
        self.save()
        if self.topic_post:
            topic = self.topic
            topic.has_attachments = self.has_attachments
            topic.has_imgs = self.has_imgs
            topic.save()

    def update_attachments(self, attachment_ids):
        self.attachments = LBAttachment.objects.filter(pk__in=attachment_ids)
        self._update_attachments_flag()

    def description(self):
            return u'%s 回复了您的话题(%s) R:《%s》' % (self.posted_by, self.topic, self.message)

    @models.permalink
    def get_absolute_url(self):
        return ('lbforum_post', (), {'post_id': self.pk})

    def get_absolute_url_ext(self):
        topic = self.topic
        post_idx = topic.posts.filter(created_on__lte=self.created_on).count()
        page = (post_idx - 1) / elp_setttings.PER_PAGE + 1
        return '%s?page=%s#p%s' % (topic.get_absolute_url(), page, self.pk)


@python_2_unicode_compatible
class OurForumUserProfile(models.Model):
    SEX_CHOICES = (
        ('F', _('Female')),
        ('M', _('Male')),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='lbforum_profile',
        verbose_name=_('User'))
    nickname = models.CharField(
        _("Nickname"), max_length=255, blank=False, default='')
    avatar = ThumbnailerImageField(_("Avatar"), upload_to='imgs/avatars', blank=True, null=True)
    bio = models.TextField(blank=True,max_length=255)
    birthday = models.DateField(verbose_name=u'生日', null=True, blank=True)

    sex = models.CharField(max_length=20, default='M', choices=SEX_CHOICES)
    class Meta:
        db_table = 'userprofile'
        verbose_name = _(u"UserProfile")
        verbose_name_plural = _(u"UserProfiles")
    def __str__(self):
        return self.nickname or self.user.username

    def get_total_topics(self):
        return self.user.topic_set.count()

    def get_total_posts(self):
        return self.user.post_set.count()

    def get_absolute_url(self):
        return self.user.get_absolute_url()

    def get_avatar_url(self, size=48):
        if not self.avatar:
            return '%s%s' % (settings.STATIC_URL, 'ourforum/imgs/avatar.png', )
        options = {'size': (size, size), 'crop': True}
        return get_thumbnailer(self.avatar).get_thumbnail(options).url

    def get_large_avatar_url(self):
        return self.get_avatar_url(80)
class Notice(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notice_sender')  # 发送者
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notice_receiver')  # 接收者
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    event = generic.GenericForeignKey('content_type', 'object_id')

    status = models.BooleanField(default=False)  # 是否阅读
    type = models.IntegerField()  # 通知类型 0:评论 1:好友消息 2:好友申请
    created_on = models.DateTimeField(auto_now_add=True, blank=True)
    updated_on = models.DateTimeField(blank=True, null=True,auto_now_add=True)
    objects = models.Manager()
    class Meta:
        db_table = 'notice'
        ordering = ['-created_on']
        verbose_name_plural = _(u"Notices")

    def __str__(self):
        return u"%s的事件: %s" % (self.sender, self.description())

    def description(self):
        if self.event:
            return self.event.description()
        return "No Event"

    def reading(self):
        if not self.status:
            status = True



def create_user_profile(sender, instance, created, **kwargs):
    if created:
        OurForumUserProfile.objects.create(user=instance)


def update_last_post(sender, instance, created, **kwargs):
    post = instance
    if created:
        topic = instance.topic
        forum = topic.forum
        topic.update_state_info(last_post=post)
        forum.update_state_info(last_post=post)

def comment_save(sender, instance, signal, created, **kwargs):
    post = instance
    if created:
       topic = instance.topic
       if str(post.created_on)[:19] == str(post.updated_on)[:19]:
           if post.posted_by != topic.posted_by:  # 作者的回复不给作者通知
               event = Notice(sender=post.posted_by, receiver=topic.posted_by, event=post, type=0)
               event.save()
               if post.comment_parent is not None:  # 回复评论给要评论的人通知
                     if post.posted_by.id != post.comment_parent.posted_by.id:  # 自己给自己写评论不通知
                        event = Notice(sender=post.posted_by, receiver=post.comment_parent.posted_by, event=post, type=0)
                        event.save()

class LoginUser(AbstractUser):
    levels = models.PositiveIntegerField(default=0,verbose_name=u'积分')
    friends = models.ManyToManyField('self', blank=True, null=True,related_name='friends')

    class Meta:
        db_table = 'loginuser'
        verbose_name_plural = _(u"User")
        ordering = ['-date_joined']

    def __unicode__(self):
        return self.get_username()

    def checkfriend(self,username):
        if username in self.friends.all():
            return True
        else:
             return False



class Message(models.Model):  # 好友消息
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='message_sender')  # 发送者
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='message_receiver')  # 接收者
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True, blank=True)
    updated_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    def description(self):
        return u'%s 给你发送了消息《%s》' % (self.sender, self.content)

    class Meta:
        db_table = 'message'
        verbose_name_plural = _(u"Messages")


class Application(models.Model):  # 好友申请
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='appli_sender')  # 发送者
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='appli_receiver')  # 接收者
    status = models.IntegerField(default=0)  # 申请状态 0:未查看 1:同意 2:不同意
    created_on = models.DateTimeField(auto_now_add=True, blank=True)
    updated_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    def description(self):
        return u'%s 申请加好友' % self.sender

    class Meta:
        db_table = 'application'
        verbose_name_plural = _(u"FriendApplications")


# class Comment(models.Model):  # 评论
#     topic = models.ForeignKey(Topic)
#     author = models.ForeignKey(settings.AUTH_USER_MODEL)
#     comment_parent = models.ForeignKey('self', blank=True, null=True, related_name='childcomment')
#     content = models.TextField()
#
#     created_on = models.DateTimeField(auto_now_add=True)
#     updated_on = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         db_table = 'comment'
#         ordering = ['created_on']
#         verbose_name_plural = u'评论'
#
#     def __str_(self):
#         return self.content
#
#     def description(self):
#         return u'%s 回复了您的话题(%s) R:《%s》' % (self.author, self.post, self.content)
#
#     @models.permalink
#     def get_absolute_url(self):
#         return ('post_detail', (), {'post_pk': self.post.pk})






def application_save(sender, instance, signal, *args, **kwargs):
    entity = instance
    if str(entity.created_on)[:19] == str(entity.updated_on)[:19]:
        event = Notice(sender=entity.sender, receiver=entity.receiver, event=entity, type=1)
        event.save()


def message_save(sender, instance, signal, *args, **kwargs):
    entity = instance
    if str(entity.created_on)[:19] == str(entity.updated_on)[:19]:
        event = Notice(sender=entity.sender, receiver=entity.receiver, event=entity, type=2)
        event.save()


from django.utils import timezone
class Bulletin_board(models.Model):
    name = models.CharField(max_length=20, verbose_name='姓名', null=False, blank=True, default="")
    email = models.EmailField(verbose_name='邮箱', null=False, blank=True, default="")
    text = models.TextField(verbose_name='留言内容', null=False, blank=True, default="")
    create_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间', null=False, blank=False)

    class Meta:
        verbose_name = _(u"Bulletin_boardcontent")
        verbose_name_plural = _(u"Bulletin_boardlist")  # 指定模型复数名称
        ordering = ['create_time']  # 按 name 字段排序
        db_table = "bulletinboard"

    # 使在后台显示的对象名称更加友好
    def __str__(self):
        return self.name




from django.db.models import signals
# 消息响应函数注册
signals.post_save.connect(comment_save, sender=Post)
signals.post_save.connect(application_save, sender=Message)
signals.post_save.connect(message_save, sender=Application)
# signals.post_save.connect(post_save, sender=Post)
# signals.post_delete.connect(post_delete, sender=Post)
signals.post_save.connect(create_user_profile, sender=LoginUser)
# post_save.connect(create_user_profile, sender=User)
signals.post_save.connect(update_last_post, sender=Post)
