"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'cci.dashboard.CustomIndexDashboard'
"""
from django.conf import Settings

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name
from settings import MCI_ETHERPAD_BASE_URL


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """
    
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        
        # append an app list module for "Applications"
        self.children.append(modules.AppList(
            _('Applications'),
            collapsible=False,
            column=1,
            css_classes=('collapse ',),
            exclude=('django.contrib.*',),
        ))

        # append a group for "Administration" & "Applications"
        self.children.append(modules.Group(
            _('Administration & Applications'),
            column=1,
            collapsible=True,
            css_classes=('collapse closed',),
            children = [
                modules.AppList(
                    _('Administration'),
                    column=1,
                    collapsible=False,
                    models=('django.contrib.*',),
                ),
                modules.AppList(
                    _('Applications'),
                    column=1,
                    css_classes=('collapse closed',),
                    exclude=('django.contrib.*',),
                )
            ]
        ))
        
        # append an app list module for "Administration"
        self.children.append(modules.ModelList(
            _('ModelList: Administration'),
            column=1,
            collapsible=True,
            css_classes=('collapse closed',),
            models=('django.contrib.*',),
        ))
        
        # append another link list module for "support".
        self.children.append(modules.LinkList(
            _('Media Management'),
            column=2,
            collapsible=False,
            children=[
                {
                    'title': _('FileBrowser'),
                    'url': '/admin/filebrowser/browse/',
                    'external': False,
                },
            ]
        ))
        
        # append another link list module for "support".
#        self.children.append(modules.LinkList(
#            _('Etherpad Management'),
#            column=3,
#            children=[
#                {
#                    'title': _('Create a new Etherpad'),
#                    'url': "%sep/pad/newpad" % MCI_ETHERPAD_BASE_URL ,
#                    'external': True,
#                },
#                {
#                    'title': _('Etherpad Administration'),
#                    'url': "%sep/admin" % MCI_ETHERPAD_BASE_URL ,
#                    'external': True,
#                },
#            ]
#        ))

        # append another link list module for "support".
        self.children.append(modules.LinkList(
            _('External Resources'),
            column=3,
            children=[
                {
                    'title': _('MIT Center for Collective Intelligence'),
                    'url': "http://cci.mit.edu/" ,
                    'external': True,
                },
                {
                    'title': _('Qualtrics Survey'),
                    'url': "http://cmu.qualtrics.com/SE?SID=SV_2ttXCnnY6OgWu2M&SVID=Prod",
                    'external': True,
                },
                {
                    'title': _('Qualtrics Intelligence Test'),
                    'url': "http://cmu.qualtrics.com/SE?SID=SV_71HOc9H0PAT1uPq&SVID=Prod",
                    'external': True,
                },
            ]
        ))

        # append another link list module for "support".
#        self.children.append(modules.LinkList(
#            _('Support'),
#            column=2,
#            children=[
#                {
#                    'title': _('Django Documentation'),
#                    'url': 'http://docs.djangoproject.com/',
#                    'external': True,
#                },
#                {
#                    'title': _('Grappelli Documentation'),
#                    'url': 'http://packages.python.org/django-grappelli/',
#                    'external': True,
#                },
#                {
#                    'title': _('Grappelli Google-Code'),
#                    'url': 'http://code.google.com/p/django-grappelli/',
#                    'external': True,
#                },
#            ]
#        ))
        
        # append a feed module
#        self.children.append(modules.Feed(
#            _('Latest Django News'),
#            column=2,
#            feed_url='http://www.djangoproject.com/rss/weblog/',
#            limit=5
#        ))
        
#        # append a recent actions module
#        self.children.append(modules.RecentActions(
#            _('Recent Actions'),
#            limit=10,
#            collapsible=False,
#            column=2,
#        ))


