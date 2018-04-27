# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
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
        verbose_name = _(u"板块类别")
        verbose_name_plural = _(u"板块类别（复数形式）")
        ordering = ('-oid', 'created_on')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Forum(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110)
    description = models.TextField(default='')
    oid = models.PositiveIntegerField(default=999)
    category = models.ForeignKey(Category,verbose_name=u"板块类别")
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
        verbose_name = _(u"板块")
        verbose_name_plural = _(u"板块（复数形式)")
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
    forum = models.ForeignKey(Forum, verbose_name=_(u'板块'))
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    class Meta:
        verbose_name = _(u"话题类型")
        verbose_name_plural = _(u"话题类型（复数形式）")
    def __str__(self):
        return self.name

LEVEL_CHOICES = (
    (30, _('Default')),
    (60, _('Distillate')),
)


@python_2_unicode_compatible
class Topic(models.Model):
    forum = models.ForeignKey(Forum, verbose_name=_(u'板块'))
    topic_type = models.ForeignKey(
        TopicType, verbose_name=_(u'话题类型'),
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
        verbose_name = '话题'
        verbose_name_plural = '话题（复数形式)'

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


@python_2_unicode_compatible
class Post(models.Model):
    FORMAT_CHOICES = (
        ('bbcode', _('BBCode')),
        ('markdown', _('Markdown')),
        ('html', _('Html')),
    )
    topic = models.ForeignKey(Topic, verbose_name=_(u'话题'), related_name='posts')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    poster_ip = models.GenericIPAddressField()
    topic_post = models.BooleanField(default=False)

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
    bio = models.TextField(blank=True)
    birthday = models.DateField(verbose_name=u'生日', null=True, blank=True)
    sex = models.CharField(max_length=20, default='M', choices=SEX_CHOICES)
    class Meta:
        db_table = 'userprofile'
        verbose_name = _(u"用户信息完善")
        verbose_name_plural = _(u"用户信息完善（复数形式）")
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

class LoginUser(AbstractUser):
    levels = models.PositiveIntegerField(default=0,verbose_name=u'积分')
    friends = models.ManyToManyField('self', blank=True, null=True,related_name='friends')

    class Meta:
        db_table = 'loginuser'
        verbose_name_plural = u'用户'
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def description(self):
        return u'%s 给你发送了消息《%s》' % (self.sender, self.content)

    class Meta:
        db_table = 'message'
        verbose_name_plural = u'消息'


class Application(models.Model):  # 好友申请
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='appli_sender')  # 发送者
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='appli_receiver')  # 接收者
    status = models.IntegerField(default=0)  # 申请状态 0:未查看 1:同意 2:不同意
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def description(self):
        return u'%s 申请加好友' % self.sender

    class Meta:
        db_table = 'application'
        verbose_name_plural = u'好友申请'


class Notice(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notice_sender')  # 发送者
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notice_receiver')  # 接收者
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    event = generic.GenericForeignKey('content_type', 'object_id')

    status = models.BooleanField(default=False)  # 是否阅读
    type = models.IntegerField()  # 通知类型 0:评论 1:好友消息 2:好友申请
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notice'
        ordering = ['-created_at']
        verbose_name_plural = u'通知'

    def __str__(self):
        return u"%s的事件: %s" % (self.sender, self.description())

    def description(self):
        if self.event:
            return self.event.description()
        return "No Event"

    def reading(self):
        if not self.status:
            status = True


def comment_save(sender, instance, signal, *args, **kwargs):
    entity = instance
    if str(entity.created_at)[:19] == str(entity.updated_at)[:19]:
        if entity.author != entity.post.author:  # 作者的回复不给作者通知
            event = Notice(sender=entity.author, receiver=entity.post.author, event=entity, type=0)
            event.save()
        if entity.comment_parent is not None:  # 回复评论给要评论的人通知
            if entity.author.id != entity.comment_parent.author.id:  # 自己给自己写评论不通知
                event = Notice(sender=entity.author, receiver=entity.comment_parent.author, event=entity, type=0)
                event.save()


def application_save(sender, instance, signal, *args, **kwargs):
    entity = instance
    if str(entity.created_at)[:19] == str(entity.updated_at)[:19]:
        event = Notice(sender=entity.sender, receiver=entity.receiver, event=entity, type=1)
        event.save()


def message_save(sender, instance, signal, *args, **kwargs):
    entity = instance
    if str(entity.created_at)[:19] == str(entity.updated_at)[:19]:
        event = Notice(sender=entity.sender, receiver=entity.receiver, event=entity, type=2)
        event.save()


# 消息响应函数注册
# signals.post_save.connect(comment_save, sender=Comment)
post_save.connect(application_save, sender=Message)
post_save.connect(message_save, sender=Application)
# signals.post_save.connect(post_save, sender=Post)
# signals.post_delete.connect(post_delete, sender=Post)
post_save.connect(create_user_profile, sender=LoginUser)
# post_save.connect(create_user_profile, sender=User)
post_save.connect(update_last_post, sender=Post)
