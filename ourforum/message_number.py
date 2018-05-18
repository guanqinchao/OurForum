from ourforum.models import Notice


# 得到消息数量设置
def messagenumber(request):
    ctx = {}
    if request.user.is_authenticated():
        k = Notice.objects.filter(receiver=request.user, is_status=False).count()
        ctx['message_number'] = k
        print(k)
    return(ctx)

# from django.db import models
#
# class UserNotificationsCount(models.Model):
#     """这个Model保存着每一个用户的未读消息数目"""
#
#     user_id = models.IntegerField(primary_key=True)
#     unread_count = models.IntegerField(default=0)
#
#     def __str__(self):
#         return '<UserNotificationsCount %s: %s>' % (self.user_id, self.unread_count)
#
#
# from django.db.models.signals import post_save, post_delete
#
#
# def incr_notifications_counter(sender, instance, created, **kwargs):
#     # 只有当这个instance是新创建，而且has_readed是默认的false才更新
#     if not (created and not instance.has_readed):
#         return
#
#     # 调用 update_unread_count 方法来更新计数器 +1
#     NotificationController(instance.user_id).update_unread_count(1)
#
#
# # 监听Notification Model的post_save信号
# post_save.connect(incr_notifications_counter, sender=Notice)
#
#
# def decr_notifications_counter(sender, instance, **kwargs):
#     # 当删除的消息还没有被读过时，计数器 -1
#     if not instance.has_readed:
#         NotificationController(instance.user_id).update_unread_count(-1)
#
#
# post_delete.connect(decr_notifications_counter, sender=Notice)
#
# from django.db import transaction
#
#
# class NotificationController(object):
#    def mark_as_readed(self, notification_id):
#         # 手动让select for update和update语句发生在一个完整的事务里面
#         with transaction.commit_on_success():
#             # 使用select_for_update来保证并发请求同时只有一个请求在处理，其他的请求
#             # 等待锁释放
#             notification = Notice.objects.select_for_update().get(pk=notification_id)
#             # 没有必要重复标记一个已经读过的通知
#             if notification.has_readed:
#                 return
#
#             notification.has_readed = True
#             notification.save()
#             # 在这里更新我们的计数器，嗯，我感觉好极了
#             self.update_unread_count(-1)