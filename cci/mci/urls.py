import views
from django.conf.urls import patterns, url, include

urlpatterns = patterns('',

    url(r'^$',
        views.home),

    url(r'^consent',
        views.consent),

    url(r'^sessionbuilder/register/(?P<sbid>\d*)',
        views.sessionbuilder_register),
    url(r'^sessionbuilder/more_info/(?P<sbid>\d*)/(?P<siid>\d*)',
        views.sessionbuilder_more_info),
    url(r'^sessionbuilder/waiting_room/(?P<sbid>\d*)/(?P<siid>\d*)',
        views.sessionbuilder_waiting_room),
    url(r'^sessionbuilder/waiting_room_checkin/(?P<sbid>\d*)/(?P<siid>\d*)',
        views.sessionbuilder_waiting_room_checkin),

    url(r'^session/register',
        views.register),
    url(r'^session/waiting_room/(?P<seid>.*)',
        views.waiting_room),
    url(r'^session/waiting_room_checkin/(?P<seid>.*)',
        views.waiting_room_checkin),

    url(r'^session/confirm_participation/(?P<seid>.*)',
        views.confirm_participation),
    url(r'^session/confirm_participation_confirm/(?P<seid>.*)',
        views.confirm_participation_confirm),
    url(r'^session/confirm_participation_checkin/(?P<seid>.*)',
        views.confirm_participation_checkin),

    url(r'^session/intro/(?P<seid>.*)',
        views.session_intro_page),

    url(r'^session/display_name/(?P<seid>.*)',
        views.session_display_name_page),
    url(r'^session/roster/(?P<seid>.*)',
        views.session_roster_page),        

    url(r'^session/preview/(?P<task_id>\d*)/I',
        views.instructions_preview, name="preview_task_instructions"),
    url(r'^session/task/(?P<ctid>\d*)/(?P<seid>.*)/I$',
        views.instructions_page),
    url(r'^session/task/(?P<ctid>\d*)/(?P<seid>.*)/I/checkin',
        views.instructions_checkin),

    url(r'^session/preview/(?P<task_id>\d*)/P',
        views.primer_preview, name="preview_task_primer"),
    url(r'^session/task/(?P<ctid>\d*)/(?P<seid>.*)/P$',
        views.primer_page),
    url(r'^session/task/(?P<ctid>\d*)/(?P<seid>.*)/P/checkin',
        views.primer_checkin),

    url(r'^session/preview/(?P<task_id>\d*)/W',
        views.workspace_preview, name="preview_task_etherpad_workspace"),
    url(r'^session/task/(?P<ctid>\d*)/(?P<seid>.*)/W$',
        views.workspace_page),
    url(r'^session/task/(?P<ctid>\d*)/(?P<seid>.*)/PP/checkin',
        views.preplay_checkin),
    url(r'^session/task/(?P<ctid>\d*)/(?P<seid>.*)/W/checkin',
        views.workspace_checkin),
    url(r'^session/task/(?P<task_id>\d*)/popup',
        views.workspace_popup),
    url(r'^session/task/results/(?P<completed_task_id>\d*)',
        views.workspace_results, name='task_results'),

    url(r'^session/task/(?P<ctid>\d*)/configureNextRound',
        views.configure_next_round),        

    url(r'^subscribed_to_stream/(?P<sub_seid>.*)/(?P<pub_seid>.*)',
        views.opentok_subscribed_to_stream),
    url(r'^published_stream/(?P<pub_seid>.*)',
        views.opentok_published_stream),

    url(r'^session/done/(?P<seid>.*)',
        views.done),
    url(r'^grid/',
        include('mci.grid.urls')),
    url(r'^reporting/',
        include('mci.reporting.urls')),
    url(r'^util/',
        include('mci.util.urls')),

    url(r'^bandwidthtest/',
        views.bandwidthtest),

    url(r'^rbtest/',
        views.rollbacktest)
)
