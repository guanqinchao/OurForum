from django.contrib.auth import authenticate, login
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
# 继承View 实现基于类的用户登陆
from django.views.generic.base import View

from lbforum.models import LoginUser

# 重写 authenticate 登陆验证方法
class CustomBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        try:
          # 验证用户名或邮箱， Q提供了一个对象间的或（与&）运算
            user=LoginUser.objects.get(Q(username=username) | Q(email=username))

            # 后台密码为暗文，传入的密码为明文， 所以需要使用check_password()方法验证密码
            if user.check_password(password):
                # 验证成功返回user对象
                return user
        # 登陆失败返回None
        except Exception as e:
            return None