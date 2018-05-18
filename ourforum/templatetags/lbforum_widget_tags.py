from django.template import Library
from django.contrib.auth import get_user_model

from ourforum.models import Topic, Category, Post
from ourforum.views import get_forum_info,get_online_ips_count
register = Library()


@register.inclusion_tag('ourforum/tags/dummy.html')
def lbf_categories_and_forums(forum=None, template='ourforum/widgets/categories_and_forums.html'):
    return {'template': template,
            'forum': forum,
            'categories': Category.objects.all()}


@register.inclusion_tag('ourforum/tags/dummy.html')
def lbf_status(template='ourforum/widgets/lbf_status.html'):
    User = get_user_model()
    ctx = {}
    ctx = get_forum_info()
    print(ctx.get('today_topic_number'))
    return {'template': template,
            'total_topics': Topic.objects.count(),
            'total_posts': Post.objects.count(),
            'total_users': User.objects.count(),
            'last_registered_user': User.objects.order_by('-date_joined').first(),
            'online_ips_count': get_online_ips_count(),
            'today_topic_number': ctx.get('today_topic_number'),
            'lastday_topic_number':ctx.get('lastday_topic_number'),
           }
