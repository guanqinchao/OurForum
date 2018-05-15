"""lbforum_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
def i18n_javascript(request):
    return admin.site.i18n_javascript(request)
urlpatterns = [
    url(r'^admin/jsi18n', i18n_javascript),
    url(r'^816/admin/', admin.site.urls),
    url(r'^', include('ourforum.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^attachments/', include('lbattachment.urls')),
    url(r'^captcha/', include('captcha.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL_, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
