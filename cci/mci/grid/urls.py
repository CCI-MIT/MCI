import views
from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^list/(?P<completed_task_id>\d*)$',views.grid_items),
                       url(r'^save$',views.save_grid_item),
                       )
