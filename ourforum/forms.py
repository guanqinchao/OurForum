# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from django import forms
from django.utils.translation import ugettext_lazy as _
from constance import config
from .models import Topic, Post, TopicType,Notice
from .models import OurForumUserProfile
from .models import Forum
from .models import Category

FORUM_ORDER_BY_CHOICES = (
    ('-last_reply_on', _('Last Reply')),
    ('-created_on', _('Last Topic')),
)


class ForumChoiceFieldMixin(object):

    def _get_choices(self):
        # def init_choices(self, have_blank=True, **kwargs):
        have_blank = True
        empty_label = self.empty_label
        categories = Category.objects.all().order_by('oid')
        choices = []
        if empty_label and have_blank:
            choices.append(['', empty_label])
        try:  # if table not existed will fail.
            for category in categories:
                choices.append(
                    (category.name, [(e.pk, e.name) for e in category.forum_set.all()])
                )
        except:
            pass
        return choices


class ForumChoiceField(ForumChoiceFieldMixin, forms.ModelChoiceField):

    choices = property(ForumChoiceFieldMixin._get_choices, None)

    def __init__(self, *args, **kwargs):
        qs = Forum.objects.all()
        self.empty_label = kwargs.pop('empty_label', '------')
        super(ForumChoiceField, self).__init__(*args, queryset=qs, **kwargs)
        # self.init_choices(True, **kwargs)


class ForumForm(forms.Form):
    order_by = forms.ChoiceField(label=_('Order By'), choices=FORUM_ORDER_BY_CHOICES, required=False)


class PostForm(forms.ModelForm):
    forum = ForumChoiceField(label=_('Forum'), required=False)
    topic_type = forms.ChoiceField(label=_('Topic Type'), required=False)
    subject = forms.CharField(label=_('Subject'), widget=forms.TextInput(attrs={'size': '80'}))
    message = forms.CharField(label=_('Message'), widget=forms.Textarea(attrs={'cols': '95', 'rows': '14'}))
    attachments = forms.Field(label=_('Attachments'), required=False, widget=forms.SelectMultiple())
    need_replay = forms.BooleanField(label=_('Need Reply'), required=False)
    need_reply_attachments = forms.BooleanField(label=_('Attachments Need Reply'), required=False)

    class Meta:
        model = Post
        fields = ('message', )

    def clean_forum(self):
        forum = self.cleaned_data['forum']
        forum = forum or self.forum
        if not forum:
            raise forms.ValidationError(_('Please chose a forum'))
        self.forum = forum
        return forum

    def clean_message(self):
        msg = self.cleaned_data['message']
        forbidden_words = config.forbidden_words
        for word in forbidden_words.split(','):
            word = word.strip()
            if word and word in msg:
                raise forms.ValidationError(_('Some word in you post is forbidden, please correct it.'))
        return msg

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.topic = kwargs.pop('topic', None)
        forum = kwargs.pop('forum', None)
        if self.topic:
            forum = self.topic.forum
        self.ip = kwargs.pop('ip', None)
        self.forum = forum or getattr(self, 'forum', None)
        super(PostForm, self).__init__(*args, **kwargs)
        if self.forum:
            topic_types = self.forum.topictype_set.all()
            self.fields['topic_type'].choices = [(tp.id, tp.name) for tp in topic_types]
            self.fields['topic_type'].choices.insert(0, (('', '--------')))
        self.fields.keyOrder = [
            'topic_type', 'subject', 'message', 'attachments', 'need_replay',
            'need_reply_attachments']


class EditPostForm(PostForm):

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance')
        initial = kwargs.pop('initial', {})
        initial['subject'] = instance.topic.subject
        self.forum = instance.topic.forum
        initial['forum'] = self.forum
        initial['need_replay'] = instance.topic.need_replay
        initial['need_reply_attachments'] = instance.topic.need_reply_attachments
        if instance.topic.topic_type:
            initial['topic_type'] = instance.topic.topic_type.id
        super(EditPostForm, self).__init__(*args, instance=instance, initial=initial, **kwargs)
        if not instance.topic_post:
            self.fields['subject'].required = False

    def save(self):
        post = self.instance
        post.message = self.cleaned_data['message']
        post.updated_on = datetime.now()
        post.edited_by = self.user.lbforum_profile.nickname
        attachments = self.cleaned_data['attachments']
        post.update_attachments(attachments)
        post.save()
        if post.topic_post:
            topic = post.topic
            topic.forum = self.forum
            topic.subject = self.cleaned_data['subject']
            topic.need_replay = self.cleaned_data['need_replay']
            topic.need_reply_attachments = self.cleaned_data['need_reply_attachments']
            topic_type = self.cleaned_data['topic_type']
            if topic_type:
                topic_type = TopicType.objects.get(id=topic_type)
            else:
                topic_type = None
            topic.topic_type = topic_type
            topic.save()
        return post


class NewPostForm(PostForm):
    def __init__(self, *args, **kwargs):
        super(NewPostForm, self).__init__(*args, **kwargs)
        if self.topic:
            self.fields['subject'].required = False

    def save(self):
        topic_post = False
        if not self.topic:
            topic_type = self.cleaned_data['topic_type']
            if topic_type:
                topic_type = TopicType.objects.get(id=topic_type)
            else:
                topic_type = None
            topic = Topic(forum=self.forum,
                          posted_by=self.user,
                          subject=self.cleaned_data['subject'],
                          need_replay=self.cleaned_data['need_replay'],
                          need_reply_attachments=self.cleaned_data['need_reply_attachments'],
                          topic_type=topic_type,
                          )
            topic_post = True
            topic.save()
        else:
            topic = self.topic
        post = Post(topic=topic, posted_by=self.user, poster_ip=self.ip,
                    message=self.cleaned_data['message'], topic_post=topic_post)
        post.save()
        if topic_post:
            topic.post = post
            topic.save()
        attachments = self.cleaned_data['attachments']
        post.update_attachments(attachments)
        return post


class SignatureForm(forms.ModelForm):
    signature = forms.CharField(
        label=_('Message'), required=False,
        widget=forms.Textarea(attrs={'cols': '65', 'rows': '4'}))

    class Meta:
        model = OurForumUserProfile
        fields = ('signature',)

from django.forms.extras.widgets import SelectDateWidget
BIRTH_YEAR_CHOICES = ('1920', '1921', '1922','1923','1924','1925','1926','1927','1928','1929',
'1930', '1931', '1932','1933','1934','1935','1936','1937','1938','1939',
'1940','1941', '1942','1943','1944','1945','1946','1947','1948','1949',
'1950', '1951', '1952','1953','1954','1955','1956','1957','1958','1959',
'1960', '1961', '1962','1963','1964','1965','1966','1967','1968','1969',
'1970', '1971', '1972','1973','1974','1975','1976','1977','1978','1979',
'1980', '1981', '1982','1983','1984','1985','1986','1987','1988','1989',
'1990', '1991', '1992','1993','1994','1995','1996','1997','1998','1999',
'2000', '2001', '2002','2003','2004','2005','2006','2007','2008','2009',
'2010', '2011', '2012','2013','2014','2015','2016','2017','2018','2019','2020',
                      )
class ProfileForm(forms.ModelForm):
    signature = forms.CharField(
        label=_('Message'), required=False,
        widget=forms.Textarea(attrs={'rows': '6'}))
    birthday = forms.DateField(widget=SelectDateWidget(years=BIRTH_YEAR_CHOICES))
    class Meta:
        model = OurForumUserProfile
        fields = ('avatar', 'nickname', 'signature', 'bio','birthday','sex')

    # def __init__(self, *args, **kwargs):
    #     super(ProfileForm, self).__init__(*args, **kwargs)
    #     self.fields['birthday'].widget = widgets.AdminDateWidget()

from ourforum.models import Message
from captcha.fields import CaptchaField
class MessageForm(forms.ModelForm):
    content = forms.CharField(label=_('Message'), widget=forms.Textarea(attrs={'cols': '55', 'rows': '14'}))

    class Meta:
        model = Message
        fields = ('content',)





