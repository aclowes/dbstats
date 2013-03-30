from django.conf.urls import patterns, url

urlpatterns = patterns('dbstats.views',
    url(r'^$', 'home'),
    url(r'^activity/$', 'activity'),
    url(r'^activity/(?P<database_id>\d+)/$', 'activity'),
    url(r'^explain/$', 'explain'),
    url(r'^explain/(?P<statement_id>\d+)/$', 'explain'),
    url(r'^settings/$', 'settings'),
    url(r'^settings/(?P<server_id>\d+)/$', 'settings'),

    # Ajax
    url(r'^activity/(?P<database_id>\d+)/graph/$', 'activity_graph'),
)
