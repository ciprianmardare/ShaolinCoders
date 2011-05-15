from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^$', 'web.views.index'),
    url(r'^accounts/', include('socialauth.urls')),
    url(r'^dashboard/', 'web.views.dashboard'),
    url(r'^logout/', 'socialauth.views.social_logout'),
    url(r'^project/create/', 'web.views.project_create'),
    url(r'^project/delete/(?P<id>[A-Za-z0-9-_]+)', 'web.views.project_delete'),
    url(r'^project/edit/(?P<id>[A-Za-z0-9-_]+)', 'web.views.project_edit'),
    url(r'^project/(?P<id>[A-Za-z0-9-_]+)', 'web.views.project'),
    url(r'^ajax/suggestions', 'web.views.ajax_suggestions'),
    url(r'^ajax/profiles', 'web.views.ajax_profiles'),
    url(r'^ajax/score', 'web.views.ajax_score'),
    url(r'^member/add/', 'web.views.member_add'),
    url(r'^member/delete/', 'web.views.member_delete'),
    url(r'^ajax/members', 'web.views.ajax_members')
)


handler404 = 'web.views.page_not_found'
handler500 = 'web.views.page_not_found'

urlpatterns += patterns('',
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT}),
)

