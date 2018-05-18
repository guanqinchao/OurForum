from django.conf.urls import url, include
from django.views.generic import TemplateView
from rest_framework import routers

from ourforum import views, profileviews
from ourforum import api
from ourforum.views import *
router = routers.DefaultRouter()
router.register(r'topic', api.TopicViewSet)

forum_patterns = [
    url(r'^(?P<forum_slug>[\w-]+)/$', views.forum, name='lbforum_forum'),
    url(r'^(?P<forum_slug>[\w-]+)/(?P<topic_type>[\w-]+)/$',
        views.forum, name='lbforum_forum'),
    url(r'^(?P<forum_slug>[\w-]+)/(?P<topic_type>[\w-]+)/(?P<topic_type2>[\w-]+)/$',
        views.forum, name='lbforum_forum'),
]

topic_patterns = [
    url('^(?P<topic_id>\d+)/$', views.topic, name='lbforum_topic'),
    url('^(?P<topic_id>\d+)/delete/$', views.delete_topic,
        name='lbforum_delete_topic'),
    url('^(?P<topic_id>\d+)/toggle_topic_attr/(?P<attr>[\w-]+)/$',
        views.toggle_topic_attr,
        name='lbforum_toggle_topic_attr'),
    url('^new/$', views.new_post, name='lbforum_new_topic'),
    url('^new/(?P<forum_id>\d+)/$', views.new_post, name='lbforum_new_topic'),
]

post_patterns = [
    url('^(?P<post_id>\d+)/$', views.post, name='lbforum_post'),
    url('^(?P<post_id>\d+)/edit/$', views.edit_post, name='lbforum_post_edit'),
    url('^(?P<post_id>\d+)/delete/$', views.delete_post,
        name='lbforum_post_delete'),
]

profile_patterns = [
    url(r'^$', profileviews.profile,
        name='lbforum_profile'),
    url(r'^(?P<user_id>\d+)/$', profileviews.profile,
        name='lbforum_profile'),
    url('^(?P<user_id>\d+)/topics/$', profileviews.user_topics,
        name='lbforum_user_topics'),
    url('^(?P<user_id>\d+)/posts/$', profileviews.user_posts,
        name='lbforum_user_posts'),
    url(r'^change/$', profileviews.change_profile,
        name='lbforum_change_profile'),
]

urlpatterns = [
    url(r'^$', views.index, name='lbforum_index'),
    url(r'^recent/$', views.recent, name='lbforum_recent'),
    url(r'^forum/', include(forum_patterns)),
    url(r'^topic/', include(topic_patterns)),
    url(r'^profile/', include(profile_patterns)),
    url(r'^api/', include(router.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^i18n/setlang', views.set_language,name='selected_language'),
    url('^reply/new/(?P<topic_id>\d+)/$', views.new_post,
        name='lbforum_new_replay'),
    url(r'^post/', include(post_patterns)),
    url(r'^lang.js$', TemplateView.as_view(template_name='ourforum/lang.js'),
        name='lbforum_lang_js'),
    url('^markitup_preview/$', views.markitup_preview,
        name='markitup_preview'),
    url(r'^makefriend/(?P<sender>\w+)/(?P<receiver>\w+)/$',  views.makefriend, name='make_friend'),
    url(r'^user/friend/(?P<pk>\d+)/(?P<flag>\d+)/$',  views.friendagree, name='friend_agree'),  # pk为对方用户id
    url(r'^user/notices/$', views.shownotice, name='show_notice'),
    url(r'^user/notices/(?P<pk>\d+)/$', views.noticedetail, name='notice_detail'),
    url(r'^user/messagedetail/(?P<pk>\d+)/$', MessageDetail.as_view(), name='message_detail'),  # pk为消息id
    url(r'^user/message/sendto/(?P<pk>\d+)/$', MessageCreate.as_view(), name='send_message'),  # pk为对方用户id
    url(r'^verify_code/$', views.verify_code,name='verify_code'),  # 配置验证码图片
    url(r'^show_verify2/$', views.show_verify2),  # 显示验证码界面
    url(r'^verify_check2/$', views.verify_check2, name='verify_check2'),  # 检测验证码
    url(r'^good/(?P<article_id>\d+)/(?P<user_id>\d+)$', views.good),
    url(r'^likes/', include('likes.urls')),
    url(r'^qwo/$', views.qwo, name='contact_us'),
    url(r'^form/', views.get_content),
]