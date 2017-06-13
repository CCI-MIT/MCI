import views
from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^audit/(?P<subject_external_id>.*)$',views.audit_entry, name="audit_entry"),
                       )
