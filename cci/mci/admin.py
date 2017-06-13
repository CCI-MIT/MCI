from django.contrib.admin.options import ModelAdmin
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q, Manager
from django.forms import ModelForm, ModelMultipleChoiceField
from django.forms.models import BaseInlineFormSet
from django.forms.widgets import TextInput, HiddenInput
from mci.models import \
    ManagerWithPermissions, \
    TaskGroup, \
    Task, \
    CompletedTask, \
    Text, \
    TaskGridItem, \
    CompletedTaskGridItem, \
    TaskPrivateInformation, \
    SessionBase, \
    Session, \
    SubjectCountry, \
    Subject, \
    Region, \
    Pseudonym, \
    SubjectIdentity, \
    DisguiseSelection, \
    SessionTemplate, \
    SessionTemplateFrequency, \
    SI_SB_Status, \
    SessionBuilder, \
    SessionRegionQuota, \
    ConcentrationCard, \
    ConcentrationRoundTemplate, \
    ConcentrationCardSet, \
    TaskConcentrationRoundTemplateIndex \
  , SquaresSet                          \
  , SquaresPiece                        \
  , SquaresRoundTemplate                \
  , TaskSquaresRoundTemplateIndex       \
  , UserGroup                           \
  , UserProfile
from mci.util import export
from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
import traceback
import logging
_log = logging.getLogger('cci')
import redis
from settings import MCI_REDIS_SERVER, MCI_REDIS_PORT
from datetime import datetime, timedelta 
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

remove_message = unicode('Hold down "Control", or "Command" on a Mac, to select more than one.')
def remove_holddown(msg):
    return unicode(msg).replace(remove_message, '').strip()

admin.site.add_action(export.admin_list_export)

class UserAdminForm(ModelForm):
    usergroups = ModelMultipleChoiceField( UserGroup.objects.all() , required=False)
    def __init__(self, *args, **kwargs):
        super(UserAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['usergroups'] = self.instance.ugroups.values_list('pk', flat=True)
    def save(self, *args, **kwargs):
        instance = super(UserAdminForm, self).save(*args, **kwargs)
        if instance.pk:
            instance.ugroups.clear()
            instance.ugroups.add(*self.cleaned_data['usergroups'])
        return instance

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    inline_classes = ('collapse open',)
    verbose_name_plural = "Other settings"

class UserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    form = UserAdminForm
    def change_view(self, request, object_id, form_url='', extra_context=None):
        this_title = unicode('User Groups (for managing object ownership)')
        if not any([unicode(title) == this_title for (title, __) in self.fieldsets]):
            self.fieldsets += ((this_title, {'fields': ('usergroups',)}),)
        return super(UserAdmin, self).change_view(request, object_id)
    def get_formsets(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if isinstance(inline, UserProfileInline) and obj is None:
                continue
            yield inline.get_formset(request, obj)

    class Media:
        css = { 'all': [ '/static/css/admin/user.css'
                       , "/static/lib/lou-multi-select-8712b02/css/multi-select.css"
                       ] }
        js = [ '/static/js/jquery-1.11.2.min.js'
             , '/static/js/grappelli-patches.js'
             , "/static/lib/lou-multi-select-8712b02/js/jquery.multi-select.js" 
             , "/static/js/admin/user.js"
             ]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class PatchedModelAdmin(admin.ModelAdmin):
    class Media:
        js = [ '/static/js/jquery-1.11.2.min.js'
             , '/static/js/grappelli-patches.js'
             , "/static/js/underscore-min.js"
             ] 
        css = {
            "all" : (
                "/static/css/admin.css",
            )
        }

class ModelAdminWithPermissions(PatchedModelAdmin):
    # Admin list view should only include permitted objects
    def get_queryset(self, request):
        return super(ModelAdminWithPermissions, self).get_queryset(request).permitted_in_change_list(request.user)

    # Admin detail views should only be available for permitted objects
    def has_permission(self, request, obj):
        if obj == None:
            return True
        return self.model.objects.permitted_in_change_list(request.user).filter(pk=obj.pk).exists()
    def has_change_permission(self, request, obj=None):
        return self.has_permission(request, obj)
    def has_delete_permission(self, request, obj=None):
        return self.has_permission(request, obj)

class ModelAdminWithPermissionsOnRelatedObjects(object):
    """ A ``ModelAdmin`` that overrides ``formfield_for_manytomany`` and
    ``formfield_for_foreignkey`` for fields whose models are instances of
    ``ManagerWithPermissions``.  These methods are on a separate class so that
    the class can be inherited by both ModelAdmins and InlineModelAdmins.
    Note that if an ``InlineModelAdmin`` is going to inherit from
    ``ModelAdminWithPermissionsOnRelatedObjects``, method
    ``get_by_modeladmin_pk`` needs to be overridden to use a QuerySet filter
    that knows how to refer to the parent form's model from the through
    model."""

    def get_by_modeladmin_pk(self, modeladmin_objects, modeladmin_obj_id):
        return modeladmin_objects.filter(pk=modeladmin_obj_id)

    def formfield_queryset(self, db_field, request, **kwargs):
        field_model = db_field.related.parent_model
        if isinstance(field_model.objects, ManagerWithPermissions):
            modeladmin_objects = db_field.related.model.objects
            try:
                modeladmin_obj_id = request.resolver_match.args[0]
            except IndexError:
                modeladmin_obj_id = None
                field_qs = field_model.objects.permitted_in_change_list(request.user)
            if modeladmin_obj_id:
                qs_selected = self.get_by_modeladmin_pk(modeladmin_objects, modeladmin_obj_id)
                existing_selection = []
                for obj_selected in qs_selected:
                    attr_val = getattr(obj_selected, db_field.name)
                    existing_selection += [obj.pk for obj in attr_val.all()] if isinstance(attr_val, Manager) else \
                                          [attr_val.pk] if attr_val else                                           \
                                          []
                field_qs = field_model.objects.permitted_in_change_list_or_selected(request.user, existing_selection)
        else:
            field_qs = field_model.objects
        return field_qs
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        #_log.debug("%s.formfield_for_manytomany >> entering..." % type(self).__name__)
        kwargs['queryset'] = self.formfield_queryset(db_field, request, **kwargs)
        ff = super(ModelAdminWithPermissionsOnRelatedObjects, self).formfield_for_manytomany(db_field, request, **kwargs)
        ff.help_text = remove_holddown(ff.help_text)
        return ff
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        #_log.debug("%s.formfield_for_foreignkey >> entering..." % type(self).__name__)
        kwargs['queryset'] = self.formfield_queryset(db_field, request, **kwargs)
        return super(ModelAdminWithPermissionsOnRelatedObjects, self).formfield_for_foreignkey(db_field, request, **kwargs)

class UserGroupAdmin(ModelAdminWithPermissionsOnRelatedObjects, ModelAdminWithPermissions):
    list_display = ['name']
    fields = ['name']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not 'users' in self.fields:
            self.fields.append('users')
        return super(UserGroupAdmin, self).change_view(request, object_id)

    class Media:
        css = {'all': ["/static/lib/lou-multi-select-8712b02/css/multi-select.css"]}
        js = [ '/static/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js'
             , '/static/js/tinymce_setup.js'
             , '//code.jquery.com/ui/1.11.2/jquery-ui.js'
             , '/static/js/admin/admin_dependencies.js'
             , "/static/lib/lou-multi-select-8712b02/js/jquery.multi-select.js"
             , '/static/js/admin/user_group.js'
             ]

admin.site.register(UserGroup, UserGroupAdmin)

# Cribbed this from
# http://stackoverflow.com/questions/2235146/adding-errors-to-django-form-errors-all
def add_form_error(obj, message):
    from django.forms.util import ErrorDict
    from django.forms.forms import NON_FIELD_ERRORS 
    if not obj._errors:
        obj._errors = ErrorDict()
    if not NON_FIELD_ERRORS in obj._errors:
        obj._errors[NON_FIELD_ERRORS] = obj.error_class()
    obj._errors[NON_FIELD_ERRORS].append(message)

# Returns True if form f had no errors and wasn't marked for deletion.
def _valid(f):
    return hasattr(f, 'cleaned_data') \
       and f.cleaned_data \
       and not f.cleaned_data.get('DELETE', False)

def _for_deletion(f):
    return hasattr(f, 'cleaned_data') \
       and f.cleaned_data \
       and f.cleaned_data.get('DELETE', False)

# Returns True if form f has any errors.
def _invalid(f):
    return bool(f.errors)

class TextAdmin(PatchedModelAdmin):
    list_display = ('key','text')
    list_editable = ('text',)

class Subject_InlineForSession(admin.TabularInline):
    model = Subject
    extra = 80 
    exclude = ['opentok_token']
    formfield_overrides = {
        models.CharField: {
            'widget': TextInput(attrs={
                'style': 'width:200px;'
            }),
        },
    }
    fields = [
        'subject_identity_link', 
        'external_id',
        'display_name',
        'country',
        'consent_and_individual_tests_completed',
        'in_waiting_room',
        'session_group',
    ]
    readonly_fields = ('subject_identity_link',)
    def subject_identity_link(self, obj):
        try:
            status = SI_SB_Status.objects.get(subject=obj)
        except SI_SB_Status.DoesNotExist:
            return None
        return "<a href='%s'>%s</a>" % (
            reverse('admin:mci_subjectidentity_change', args=(status.subject_identity.id,)),
            status.subject_identity)
    subject_identity_link.allow_tags = True

class SubjectCountryAdmin(PatchedModelAdmin):
    model = SubjectCountry
    list_display = ('__unicode__', 'thumbnail')

class SubjectAdmin(ModelAdminWithPermissionsOnRelatedObjects, ModelAdminWithPermissions):
    fields = [
        'session_link',
        'external_id',
        'display_name',
        'country_link',
        'consent_and_individual_tests_completed',
        'in_waiting_room',
        'scribe',
        'session_group',
        'opentok_token',
    ]           
    list_display = [
        'external_id',
        'session_link',
        'consent_and_individual_tests_completed',
        'country_link',
    ]
    list_filter =  [
        'session',
        'country',
        'consent_and_individual_tests_completed',
    ]
    readonly_fields = [
        'session_link',
        'country_link',
        'opentok_token',
    ]
    def session_link(self, obj):
        return "<a href='%s'>%s</a>" % (
            reverse('admin:mci_session_change', args=(obj.session.id,)),
            obj.session)
    session_link.allow_tags = True
    def country_link(self, obj):
        if obj.country and obj.country.id:
            return "<a href='%s'>%s</a>" % (
                reverse('admin:mci_subjectcountry_change', args=(obj.country.id,)),
                obj.country)
        else:
            return ""
    country_link.allow_tags = True

class SI_SB_Status_InlineForSB(admin.TabularInline):
    model = SubjectIdentity.sessionbuilders.through
    verbose_name = "Registered Subject Identity" 
    verbose_name_plural = "Registered Subject Identities" 
    extra = 0
    max_num = 0
    fields = [
        'subject_identity_link',
        'display_name', 
        'compatibility_check',
        'arrival', 
        'last_waiting_rm_checkin',
        'rejected',
        'rejection_reason',
        'session',
    ]
    readonly_fields = [
        'subject_identity_link',
        'display_name', 
        'compatibility_check',
        'arrival', 
        'last_waiting_rm_checkin',
        'rejected',
        'rejection_reason',
        'session',
    ]

    def subject_identity_link(self, obj):
        return "<a href='%s'>%s</a>" % (
            reverse('admin:mci_subjectidentity_change', args=(obj.subject_identity.id,)),
            obj.subject_identity)
    subject_identity_link.allow_tags = True
    def display_name(self, obj):
        return obj.subject_identity.display_name
    def compatibility_check(self, obj):
        rc = redis.Redis(host=MCI_REDIS_SERVER, port=MCI_REDIS_PORT)
        stamp = rc.get("sbregping_%d" % obj.subject_identity.pk)        
        return datetime.fromtimestamp(int(stamp) / 1000).strftime('%b %d %I:%M:%S %p') if stamp else ""
    def arrival(self, obj):
        return obj.arrival_time.strftime('%b %d %I:%M:%S %p')
    arrival.allow_tags = True
    def last_waiting_rm_checkin(self, obj):
        return obj.last_waiting_room_checkin.strftime('%b %d %I:%M:%S %p')
    last_waiting_rm_checkin.allow_tags = True
#    def country(self, obj):
#        return "<a href='%s'>%s</a>" % (
#            reverse('admin:mci_subjectcountry_change', args=(obj.subject_identity.country.id,)),
#            obj.subject_identity.country)
#    country.allow_tags = True
    def session(self, obj):
        if not obj.subject:
            return None
        return "<a href='%s'>%s</a>" % (
            reverse('admin:mci_session_change', args=(obj.subject.session.id,)),
            obj.subject.session)
    session.allow_tags = True
#    def subject(self, obj):
#        if not obj.subject:
#            return None
#        return "<a href='%s'>%s</a>" % (
#            reverse('admin:mci_subject_change', args=(obj.subject.id,)),
#            obj.subject)
#    subject.allow_tags = True 

class SI_SB_Status_InlineForSubjectIdentity(admin.TabularInline):
    model = SubjectIdentity.sessionbuilders.through 
    verbose_name = "Status vis-a-vis a specific Session Builder"
    verbose_name_plural = "Statuses vis-a-vis specific Session Builders"
    extra = 0
    max_num = 0
    fields = [
        'sessionbuilder_link',
        'arrival_time', 
        'dispatch_time',
        'external_id',
        'session',
    ]
    readonly_fields = [
        'sessionbuilder_link',
        'arrival_time', 
        'dispatch_time',
        'external_id',
        'session',
    ]
    def sessionbuilder_link(self, obj):
        return "<a href='%s'>%s</a>" % (
            reverse('admin:mci_sessionbuilder_change', args=(obj.sessionbuilder.id,)),
            obj.sessionbuilder)
    sessionbuilder_link.allow_tags = True
    def external_id(self, obj):
        return obj.subject
    def session(self, obj):
        if not obj.subject:
            return None
        return "<a href='%s'>%s</a>" % (
            reverse('admin:mci_session_change', args=(obj.subject.session.id,)),
            obj.subject.session)
    session.allow_tags = True

class DS_Inline_Form(ModelForm):
    class Meta:
        model = DisguiseSelection 

    def custom_is_valid(self):
        valid = True
        # This assumes we have passed the 'clean' stage and this form is valid.
        cleaned_data = self.clean()
        # The DisguiseSelection's Region must have at least one SubjectCountry.
        try:
            region = cleaned_data['region']
            if region.countries.count() == 0:
                region_link = "<a href='%s'>%s</a>" % (
                    reverse('admin:mci_region_change', args=(region.id,)),
                    region)
                add_form_error(self, mark_safe("""Region %s must have at least one
                    Country associated with it.""" % region_link))
                valid = False
        except Region.DoesNotExist:
            pass
        return valid

class DS_Inline_Formset(BaseInlineFormSet):
    def clean(self): 
        submitted_forms = [f for f in self.forms if _valid(f) or _invalid(f)]
        # If the Session form's 'subjects_disguised' field is unchecked,
        # that field doesn't even appear in the form data QueryDict.
        if 'subjects_disguised' in self.data:
            valid_forms = [f for f in self.forms if _valid(f)]
            if valid_forms:
                # Run more validation on the individual forms. 
                all_valid = all([f.custom_is_valid() for f in valid_forms])
                if not all_valid:
                    raise ValidationError("")
                # Each Region used by any of our DisguiseSelections must
                # have enough Pseudonyms to meet the aggregate requirements
                # of this Session -- or, as the case may be, of this
                # SessionTemplate in combination with each of the
                # SessionBuilders that use it.
                unsaved_dss = [f.save(commit=False) for f in valid_forms]
                unmet_req_reports = self.instance.nym_shortfall_reports(unsaved_dss)
                if unmet_req_reports:
                    raise ValidationError(mark_safe(unmet_req_reports))
        else:
            if submitted_forms:
                raise ValidationError(""" If we're not going to disguise subjects,
                    you must not make any Disguise Selections. """)

class DS_Inline_ForSession_Formset(DS_Inline_Formset):
    def clean(self):
        # First, check whether self.session is just a default Session object --
        # which is what it is if the Session form was submitted with invalid
        # data.  In that case, we don't want to try to validate the inline
        # forms.  It would only confuse the user, especially since some of our
        # validations take into account the values on self.instance.
        # Note that it doesn't matter whether the Session is *saved* yet,
        # only whether it's valid.
        session = self.instance
        if not session.max_group_size:
            return
        if 'subjects_disguised' in self.data:
            submitted_forms = [f for f in self.forms if _valid(f) or _invalid(f)] 
            # The number of Disguise Selections must be at least
            # session.max_group_size - 1.
            if len(submitted_forms) < session.max_group_size - 1:
                raise ValidationError("""This Session might use up to %d
                    disguises.""" % (session.max_group_size - 1))
        super(DS_Inline_ForSession_Formset, self).clean()

class DS_Inline_ForSessionTemplate_Formset(DS_Inline_Formset):
    def clean(self):
        # First, check whether the SessionTemplate whose Inline formset this is
        # has a pk.  If not, then it's being newly created and so it isn't
        # possible that any SessionBuilders yet expect to use it, which means
        # it doesn't impose concrete requirements on any Regions yet.
        st = self.instance
        if st.pk:
            if 'subjects_disguised' in self.data:
                submitted_forms = [f for f in self.forms if _valid(f) or _invalid(f)] 
                # The number of Disguise Selections must be at least the
                # (subjects_per_session - 1) value of the related Session Builder
                # with the largest (subjects_per_session) value.
                reports = st.unmet_ds_requirement_reports(len(submitted_forms))
                if reports:
                    raise ValidationError(mark_safe(reports))
        super(DS_Inline_ForSessionTemplate_Formset, self).clean()


class DS_Inline(admin.TabularInline):
    verbose_name = "Disguise Type"
    verbose_name_plural = "Disguise Types to be Used"
    extra = 0
    fields = [
        'region', 
        'feminine',
        'position',
    ]
    sortable_field_name = 'position'
    formset = DS_Inline_Formset
    form = DS_Inline_Form

    class Media:
        js = [
            '/static/js/jquery-1.11.2.min.js',
            '/static/js/grappelli-patches.js',
        ]

class DS_Inline_ForSession(DS_Inline):
    model = Session.disguise_regions.through
    formset = DS_Inline_ForSession_Formset

class DS_Inline_ForSessionTemplate(DS_Inline):
    model = SessionTemplate.disguise_regions.through
    formset = DS_Inline_ForSessionTemplate_Formset

class SessionBaseAdmin(ModelAdminWithPermissionsOnRelatedObjects, ModelAdminWithPermissions):
    def get_fieldsets(self, request, obj=None):
        fieldsets = super(SessionBaseAdmin, self).get_fieldsets(request, obj)
        if not request.user.is_superuser:
            fieldsets[0][1]['fields'] = [f for f in fieldsets[0][1]['fields'] if not f == "load_test"]
        return fieldsets

    class Media:
        js = [ '/static/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js'
             , '/static/js/tinymce_setup.js'
             , '/static/js/admin/video_inversion.js'
             , '//code.jquery.com/ui/1.11.2/jquery-ui.js'
             , '/static/js/admin/admin_dependencies.js'
             , "/static/lib/lou-multi-select-8712b02/js/jquery.multi-select.js"
             , '/static/js/admin/session_base.js'
             ]
        css = { 'all': [ "/static/lib/lou-multi-select-8712b02/css/multi-select.css" ] }

class SessionTemplateAdmin(SessionBaseAdmin):
    list_display = [
        'name',
        'video_enabled',
        'subjects_disguised',
    ]
    fieldsets = (
        ('Basics', {
            'fields': (
                'name', 'load_test', 'usergroups',
            )
        }),
        ('Session Intro', {
            'fields': ( 'introduction_text'
                      , 'introduction_time'
                      , 'display_name_page'
                      , 'display_name_time'
                      , 'roster_page'
                      , 'roster_time'
                      ),
        }),
        ('Done Page', {
            'fields': (
                'done_text', 'done_time', 'done_redirect_url',
            ),
        }),
        ('Error Messages', {
            'fields': (
                'msg_err_cannot_form_group',
            ),
        }),
        ('Task Groups', {
            'fields': (
                'solo_task_group_start', 
                'initial_task_group',
                'task_groups',
                'solo_task_group_end',
            ),
        }),
        ('Disguise Settings', {
            'fields': (
                'video_enabled',
                'subjects_disguised',
            )
        }),
    )
    inlines = [ DS_Inline_ForSessionTemplate ] 

class STFInline_ForSB_Form(ModelForm):
    def custom_is_valid(self):
        valid = True
        cleaned_data = super(STFInline_ForSB_Form, self).clean()
        # Require that field 'Frequency' be on the interval (0.0, 1.0].
        freq = self.cleaned_data['frequency']
        if (not freq > 0.0) or freq > 1.0:
            add_form_error(self, """ 'Frequency' must be greater than 0.0 and
                at most 1.0. """)
            valid = False
        sb = self.cleaned_data['session_builder']
        st = self.cleaned_data['session_template']
        not_enough_ds_report = sb.unmet_ds_requirement_report_for_st(st)
        if not_enough_ds_report:
            add_form_error(self, mark_safe(not_enough_ds_report))
            valid = False
        # Each Region used by each of this SessionBuilder's SessionTemplates
        # must have enough Pseudonyms to meet the requirements imposed by the
        # SB/ST combo.
        unmet_req_reports = st.unmet_nym_req_reports_for_session_template_given_sb(sb)
        if unmet_req_reports:
            add_form_error(self, mark_safe(unmet_req_reports))
            valid = False
        return valid

    def valid_for_deletion(self):
        valid = True
        # Require that this STF not be deleted if a SI_SB_Status is related to it.
        if 'id' in self.cleaned_data and self.cleaned_data['id'].pk:
            pk = self.cleaned_data['id'].pk
            if Session.objects.filter(session_template_frequency__pk=pk).count():
                m = """You can't delete this Session Template from
                the list of STs used by this Session Builder --
                we've already spun off at least one Session using
                it."""
                add_form_error(self, mark_safe(m))
                valid = False
        return valid

class STFInline_ForSB_Formset(BaseInlineFormSet):
    def clean(self):
        # First, check whether self.session_builder is just a default Session
        # object -- which is what it is if the SessionBuilder form was submitted
        # with any invalid data.  In that case, we don't want to try to
        # validate the inline forms.  It would only confuse the user,
        # especially since some of our validations take into account the values
        # on self.instance.
        session_builder = self.instance
        if not session_builder.subjects_per_session:
            return
        submitted_forms = [f for f in self.forms if _valid(f) or _invalid(f)]
        if submitted_forms:
            valid_forms = [f for f in self.forms if _valid(f)]
            if valid_forms:
                uniques = set([f.cleaned_data['session_template']
                               for f in valid_forms])
                if len(uniques) != len(valid_forms):
                    raise ValidationError(""" You cannot select any Session
                        Template more than once. """)                
                if sum([f.cleaned_data['frequency'] for f in valid_forms]) != 1.0:
                    raise ValidationError(""" The 'Frequency' fields on our
                        SessionTemplate selections must sum to 1.0. """)
                # Run more validation on our individual forms. 
                all_valid = all([f.custom_is_valid() for f in valid_forms])
                if not all_valid:
                    raise ValidationError("")
        else:
            # Require at least 1 SessionTemplate.
            raise ValidationError(""" You must select at least one
                SessionTemplate for use with this SessionBuilder. """)
        # We need to make sure we don't delete STFs that were used already
        # to spin off Sessions.  The reason: there's an SI_SB_Status related to
        # each Session, and the FK relationships mean the deletes will cascade.  But
        # we're submitting a form that assumes the existence of all the SI_SB_Status
        # objects that existed when the form was first generated.
        forms_for_deletion = [f for f in self.forms if _for_deletion(f)]
        all_deletions_valid = all([f.valid_for_deletion() for f in forms_for_deletion])
        if not all_deletions_valid:
            raise ValidationError("")
          
class STFInline_ForSB(ModelAdminWithPermissionsOnRelatedObjects, admin.StackedInline):
    model = SessionBuilder.session_templates.through
    verbose_name_plural = "Session Templates to use on a rotating basis"
    verbose_name = "Session Template"
    extra = 0
    formset = STFInline_ForSB_Formset
    form = STFInline_ForSB_Form
    classes = ('collapse open',)
    inline_classes = ('collapse open',)
    fields = [
        'session_template',
        'session_template_link',
        'frequency',
        'disguises_to_be_used',
    ]
    readonly_fields = [
        'session_template_link',
        'disguises_to_be_used',
    ]

    def get_by_modeladmin_pk(self, modeladmin_objects, modeladmin_obj_id):
        return modeladmin_objects.filter(session_builder__pk=modeladmin_obj_id)

    def session_template_link(self, obj):
        return '<a href="%s">%s</a>' % (
            reverse('admin:mci_sessiontemplate_change', args=(obj.session_template.id,)),
            obj.session_template.name)
    session_template_link.allow_tags = True
    session_template_link.short_description = "Link"

    def disguises_to_be_used(self, obj):
        dss = obj.session_template.disguise_selections.all(
            ).order_by('position')[:obj.session_builder.subjects_per_session - 1]
        html = '<ul>%s</ul>' % ''.join([
            '<li>%s / %s</li>' % (
                "<a href='%s'>%s</a>" % (
                    reverse('admin:mci_region_change', args=(ds.region.id,)),
                    ds.region),
                "Fem" if ds.feminine else "Masc",
            ) for ds in dss
        ])
        return mark_safe(html)
    disguises_to_be_used.allow_tags = True

class SessionRegionQuota_Inline_Formset(BaseInlineFormSet):
    def clean(self):
        # First, check whether self.session is just a default SessionBuilder
        # object -- which is what it is if the SessionBuilder form was
        # submitted with invalid data.  In that case, we don't want to try to
        # validate the inline forms.  It would only confuse the user,
        # especially since some of our validations take into account the values
        # on self.instance.
        session_builder = self.instance
        if not session_builder.subjects_per_session:
            return
        # Don't report any formset-level errors until all individual forms
        # are valid.  TODO: this is kind of crappy.  Reporting formset-level
        # errors *first* is the way we do it with DS_Inline, and with good
        # reason.  But here we do it this way, in the interest of saving time.
        if self.errors:
            return
        valid_forms = [f for f in self.forms if _valid(f)]
        # \ total number of Subjects accounted for by these SRQs. \
        quota_sum = sum([f.cleaned_data['subjects'] for f in valid_forms])
        if quota_sum > session_builder.subjects_per_session:
            raise ValidationError(""" The number of spots accounted for by your
                Region Quotas must not exceed Subjects Per Session. """)

class SessionRegionQuota_Inline(admin.TabularInline):
    model = SessionRegionQuota 
    extra = 0
    verbose_name = "Region Quota"
    verbose_name_plural = "Region Quotas (for actual subjects, not disguises)"
    formset = SessionRegionQuota_Inline_Formset

class SessionBuilderAdmin(ModelAdminWithPermissionsOnRelatedObjects, ModelAdminWithPermissions):
    list_display = (
        'name', 
        'mturk', 
        'waiting_room_opens',
        'waiting_room_closes',
        'subjects_per_session',
        'start_url',
    )
    actions = ['copy_session_builder']
    fieldsets = (
        ('Basics', {
            'fields': (
                'name',
                'start_url',
                'waiting_room_opens', 
                'waiting_room_closes', 
                'mturk',
                'custom_id_label',
                'ask_for_group_id',
            ),
        }),
        ('Criteria for subject sets', {
            'fields': (
                'subjects_per_session',
                'previous_play_required',
                'previous_play_forbidden',
            ),
        }),
        ('Messages', {
            'fields': (
                'javascript_test_explanation',
                'error_connecting_to_game_server_msg',
            ),
        }),
        ('Permissions', { 'fields': [ 'usergroups' ] }),
    )
    readonly_fields = ('start_url',)
    inlines = [ SessionRegionQuota_Inline
              , STFInline_ForSB
              , SI_SB_Status_InlineForSB
              ]

    def start_url(self, obj):
        login_url = reverse('mci.views.sessionbuilder_register', kwargs={
            "sbid" : obj.id, 
        })
        return "<a href='%s'>Login URL</a>" % login_url
    start_url.allow_tags = True
    start_url.short_description = "Login URL"

    def copy_session_builder(self, request, queryset):
        import copy
        for sb in queryset:
            new_sb = copy.deepcopy(sb)
            new_sb.save()
        self.message_user(request, "Session Builder(s) copied")

    class Media:
        css = { 'all': [ '/static/css/admin_sessionbuilder.css'
                       , "//code.jquery.com/ui/1.11.2/themes/smoothness/jquery-ui.css"
                       , "/static/lib/lou-multi-select-8712b02/css/multi-select.css"
                       ]
              }
        js = [ '//code.jquery.com/ui/1.11.2/jquery-ui.js'
             , '/static/js/admin/admin_dependencies.js'
             , '/static/js/admin/custom_id_label.js'
             , "/static/lib/lou-multi-select-8712b02/js/jquery.multi-select.js"
             , "/static/js/admin/session_builder.js"
             ]
 
class SessionAdmin(SessionBaseAdmin):

    list_display = [
        'name',
        'status',
        'start_datetime',
        'min_group_size',
        'max_group_size',
        'subject_count',
        'task_groups_list',
        'builder',
        'template',
        'subjects_disguised',
        'video_enabled',
        'log',
        'metadata',
        'zip',
    ]
    exclude = ['opentok_session_id']    
    fieldsets = (
        ('Basics', {
            'fields': (
                'name',
                'start_datetime',
                'status',
                'reset_link',
                'min_group_size',
                'max_group_size',
                'group_creation_method',
                'group_creation_matrix',
                'scribe_enabled',
                'confirmation_required',
                'waiting_room_time',
                'builder',
                'template',
                'load_test',
                'usergroups',
            ),
        }),
        ('Session Intro', {
            'fields': (
                'introduction_text',
                'introduction_time',
                'display_name_page',
                'display_name_time',
                'roster_page',
                'roster_time',
            ),
        }),
        ('Done Page', {
            'fields': (
                'done_text',
                'done_time',
                'done_redirect_url',
            ),
        }),
        ('Error Messages', {
            'fields': (
                'msg_err_cannot_form_group',
            ),
        }),
        ('Task Groups', {
            'fields': (
                'solo_task_group_start',
                'initial_task_group',
                'task_groups',
                'solo_task_group_end',
             ),
        }),
        ('Deception', {
            'fields': (
                'subjects_disguised',
                'video_enabled',
            ),
        }),
    )
    readonly_fields = (
        'builder',
        'template',
        'reset_link',
    )
    inlines = [ DS_Inline_ForSession
              , Subject_InlineForSession
              ]
    save_as = True
    actions = ['reset_session', 'copy_session', 'start_session']

    # Hide tinyMCE for the matrix field
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(SessionAdmin, self).formfield_for_dbfield(db_field,**kwargs)
        if db_field.name == 'group_creation_matrix':
            field.widget.attrs['class'] = 'mceNoEditor ' + \
                                           field.widget.attrs.get('class', '')
        return field

    def builder(self, obj):
        if not obj.session_template_frequency:
            return ''
        sb = obj.session_template_frequency.session_builder
        return "<a href='%s'>%s</a>" % (
            reverse('admin:mci_sessionbuilder_change', args=(sb.id,)),
            sb)
    builder.allow_tags = True

    def template(self, obj):
        if not obj.session_template_frequency:
            return ''
        st = obj.session_template_frequency.session_template
        return "<a href='%s'>%s</a>" % (
            reverse('admin:mci_sessiontemplate_change', args=(st.id,)),
            st)
    template.allow_tags = True

    def reset_session(self, request, queryset):
        for obj in queryset:
            obj.reset()
        self.message_user(request, "Session(s) reset")
    reset_session.short_description = "Reset selected sessions"

    def copy_session(self, request, queryset):
        import copy
        for obj in queryset:
            new_obj = copy.deepcopy(obj)
            new_obj.save()
        self.message_user(request, "Session(s) copied")
    copy_session.short_description = "Copy selected sessions"

    def start_session(self, request, queryset):
        for obj in queryset:
            obj.min_group_size = min(obj.min_group_size,
                                     obj.subject_set.filter(
                                        in_waiting_room__exact=True).count())
            obj.start_now()
            obj.save()
        self.message_user(request, "Session(s) set to start in 20 seconds")
    start_session.short_description = "Start selected sessions now"

    def log(self,obj):

        def url(i):
            return reverse( 'session_log'
                          , kwargs={ 'session_id'    : obj.id
                                   , "session_group" : i      })
        def link(i):
            return "<a href='%s'>Group %s</a>" % (url(i), i)

        def export_url(i):
            return reverse( 'session_log_export'
                          , kwargs={ 'session_id'    : obj.id
                                   , "session_group" : i      })
        def export_link(i):
            return "<a href='%s'>Group %s</a>" % (export_url(i), i)

        group_indices = obj.session_groups()
        if len(group_indices) > 1:
            links        = map(link,        group_indices)
            export_links = map(export_link, group_indices)

            return "Log ("    + ", ".join(links)        + ") | " + \
                   "Export (" + ", ".join(export_links) + ")"
        else:
            return "<a target='_blank' href='%s'>Log</a> (<a href='%s'>Export</a>)" % \
                (url(1), export_url(1))
    log.allow_tags = True

    def metadata(self, obj):

        def url(i):
            return reverse( 'session_metadata_export'
                          , kwargs={ 'session_id'    : obj.id
                                   , 'session_group' : i      })
        def link(i):
            return "<a href='%s'>Group %s</a>" % (url(i), i)

        group_indices = obj.session_groups()
        if len(group_indices) > 1:
            export_links = map(link, group_indices)
            return "Export (" + (", ".join(export_links)) + ")"
        else:
            return "<a target='_blank' href='%s'>Export</a>" % url(1)
    metadata.allow_tags = True

    def zip(self, obj):
        group_indices = obj.session_groups()
        if len(group_indices) > 0:
            url = reverse( 'session_zip_export'
                         , kwargs={ 'session_id' : obj.id }
                         )
            return "<a target='_blank' href='%s'>Export</a>" % url
        else: return ''
    zip.allow_tags = True

    def reset_link(self, obj):
        if obj.pk:
            return "<a href='%s'>Reset</a>" % reverse(
                'session_reset',
                args=(obj.id,))
            return "(can't reset until saved)"
    reset_link.allow_tags = True
    
class SubjectCountryInline(admin.TabularInline):
    model = Region.countries.through

class PseudonymInline_ForRegion_Formset(BaseInlineFormSet):
    # Verify that the current form submission will leave this Region with
    # enough masculine and feminine Pseudonyms to meet the expectations of all
    # (1) Sessions and (2) SessionBuilder/SessionTemplate combos that expect to
    # use disguises from the Region.
    def clean(self):
        try:
            # Does the Region whose Inline formset this is have a pk?  (If not,
            # then it's being newly created and so it isn't possible that any
            # Sessions or SessionTemplates yet expect to use its Pseudonyms.)
            region = self.instance
            if region.pk:
                # \ list of forms representing Pseudonym objects that will exist
                #   (linked to this Region) if this Inline formset submission is
                #   allowed. \
                remaining = [f for f in self.forms
                               if  f.cleaned_data
                               and not f.cleaned_data.get('DELETE', False)]
                # \ numbers of feminine and masculine Pseudonyms this Region will
                #   have if the current Inline formset submission is allowed. \ 
                f_ct = len([f for f in remaining if f.cleaned_data['feminine']])
                m_ct = len(remaining) - f_ct
                # \ Now the payoff: we find out which if any SessionBuilders expect
                #   this Region to have more Pseudonyms than it will if we approve
                #   the current form submission.  If any do, we don't approve it. \
                reports = region.unmet_nym_req_reports_given_new_counts(f_ct, m_ct)
                if reports:
                    raise ValidationError(mark_safe(reports))
        except AttributeError:
            # This happens when one of the individual forms in the formset
            # failed validation.  If that's the case, the object representing
            # that failed form won't have a cleaned_data attribute.  The upshot
            # is that we can't do formset-level validation until the individual
            # forms are all validated.
            pass

class PseudonymInline_ForRegion(admin.TabularInline):
    model = Pseudonym
    formset = PseudonymInline_ForRegion_Formset
    extra = 0

class RegionAdmin(PatchedModelAdmin):
    model = Region
    fields = ('name',)
    inlines = [
        SubjectCountryInline,
        PseudonymInline_ForRegion,
    ]
    class Media:
        js = [
            '/static/js/jquery-1.11.2.min.js',
            '/static/js/grappelli-patches.js',
        ]

class SubjectIdentityAdmin(ModelAdminWithPermissionsOnRelatedObjects, ModelAdminWithPermissions):
    model = SubjectIdentity 
    inlines = [
        SI_SB_Status_InlineForSubjectIdentity,
    ]

class TaskGridItemAdmin(ModelAdminWithPermissionsOnRelatedObjects, ModelAdminWithPermissions):
    list_display = [ 'task'
                   , 'task_group_link'
                   , 'row'
                   , 'column'
                   ]
    def task_group_link(self, obj):
        url = reverse( 'admin:mci_taskgroup_change'
                     , args=(obj.task.task_group.id,)
                     )
        return "<a href='%s'>%s</a>" % (url, obj.task.task_group)
    task_group_link.allow_tags = True
    task_group_link.short_description = "Task Group"

class TaskGridItemInline(admin.TabularInline):
    model = TaskGridItem
    formfield_overrides = {
        models.IntegerField: {'widget': TextInput(attrs={'style':'width:35px;'})},
        models.CharField: {'widget': TextInput(attrs={'style':'width:200px;'})}
    }

class TaskPrivateInformationInline(admin.TabularInline):
    model = TaskPrivateInformation
    

class TaskInline(admin.StackedInline):
  model = Task
  sortable_field_name = 'task_order'
  extra = 0


class TaskConcentrationRoundTemplateIndexInline(admin.TabularInline):
    model = TaskConcentrationRoundTemplateIndex
    extra = 0
    verbose_name = 'Concentration Round'
    verbose_name_plural = 'Concentration Rounds'
    sortable_field_name = 'position'

class TaskSquaresRoundTemplateIndexInline(admin.TabularInline):
    model = TaskSquaresRoundTemplateIndex
    extra = 0
    verbose_name = 'Squares Round'
    verbose_name_plural = 'Squares Rounds'
    sortable_field_name = 'position'

class TaskAdmin(ModelAdminWithPermissionsOnRelatedObjects, ModelAdminWithPermissions):
    list_display = [ 'name'
                   , 'task_group'
                   , 'task_order'
                   , 'task_type'
                   , 'preview_instructions'
                   , 'preview_primer'
                   , 'edit_workspace'
                   ]
    export_fields = ('name', 'task_group', 'task_order', 'task_type')
    list_filter = ['task_group']
    save_as = True
    fieldsets = (
        (None, {
            'fields' : ('name', 'task_group', 'task_order', 'task_type',
                        'time_between_rounds',
                        'time_unmatched_pairs_remain_faceup',
                        'pairs_in_generated_round', 'chat_enabled')
        }),
        ('Instructions', {
            'fields' : ('instructions', 'instructions_time')
        }),
        ('Primer', {
            'fields' : ('primer', 'primer_sidebar_text', 'primer_time')
        }),
        ('General Workspace', {
            'fields' :
                [ 'time_before_play'
                , 'preplay_countdown_sublabel'
                , 'starting_width'
                , 'starting_height'
                , 'pct_tiles_on'
                , 'tiles_preview_seconds'
                , 'interaction_instructions'
                , 'interaction_time'
                , 'instructions_width'
                ]
        }),
        ('Grid Workspace', {
            'classes' : ('collapse', 'fieldset-grid-workspace'),
            'fields' : ('grid_header_instructions','grid_css')
        }),
    )
    inlines = [ TaskPrivateInformationInline
              , TaskGridItemInline
              , TaskConcentrationRoundTemplateIndexInline
              , TaskSquaresRoundTemplateIndexInline
              ]

    # Hide tinyMCE for the grid_css field
    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(TaskAdmin, self).formfield_for_dbfield(db_field,**kwargs)
        if db_field.name == 'grid_css':
            field.widget.attrs['class'] = 'mceNoEditor ' + \
                                           field.widget.attrs.get('class', '')
        return field

    def _get_preview_url(self, view_name, label, obj):
        return '<a target="_blank" href="%s">%s</a>' % (reverse(
        viewname=view_name, kwargs={
            'task_id': obj.id}),
        label)

    def preview_instructions(self,obj):
        return self._get_preview_url(
        'preview_task_instructions',
        'Preview Instructions',
        obj)
    preview_instructions.allow_tags = True

    def preview_primer(self,obj):
        return self._get_preview_url(
        'preview_task_primer',
        'Preview Primer',
        obj) if obj.primer else ""
    preview_primer.allow_tags = True

    def edit_workspace(self,obj):
        label = "Edit Workspace" if (obj.task_type == "T") else "Preview Workspace"
        return self._get_preview_url('preview_task_etherpad_workspace', label, obj) \
                     if     (obj.etherpad_template or obj.task_type == "G") \
                     else    ""
    edit_workspace.allow_tags = True

    class Media:
        css = { 'all' : [ "//code.jquery.com/ui/1.11.2/themes/smoothness/jquery-ui.css" ] }
        js = [ '/static/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js'
             , '/static/js/tinymce_setup.js'
             , '//code.jquery.com/ui/1.11.2/jquery-ui.js'
             , '/static/js/admin/admin_dependencies.js'
             , '/static/js/admin/task_admin.js'
             ]

class TaskGroupAdmin(ModelAdminWithPermissionsOnRelatedObjects, ModelAdminWithPermissions):
    fields = ['name', 'usergroups']
    inlines = [TaskInline]
    class Media:
        css = {'all': ["/static/lib/lou-multi-select-8712b02/css/multi-select.css"]}
        js = [ '/static/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js'
             , '/static/js/tinymce_setup.js'
             , '//code.jquery.com/ui/1.11.2/jquery-ui.js'
             , '/static/js/admin/admin_dependencies.js'
             , "/static/lib/lou-multi-select-8712b02/js/jquery.multi-select.js"
             , '/static/js/admin/task_group_admin.js'
             ]

class CompletedTaskAdmin(ModelAdminWithPermissionsOnRelatedObjects, ModelAdminWithPermissions):
    list_display = [
        'session',
        'task_link', 
        'session_group',
        'completed_task_order', 
        'start_time', 
        'etherpad_workspace_url',
        'results', 
        'log',
        'contents_txt',
    ]
    readonly_fields = (
        'session',
        'task_link',
        'session_group',
        'completed_task_order',
        'start_time',
        'etherpad_workspace_url',
        'contents_txt',
    )
    list_filter = [
        'session',
        'task',
        'session_group',
    ]
    export_fields = [
        'session',
        'task',
        'session_group',
        'completed_task_order',
        'start_time', 
        'etherpad_workspace_url', 
        'grid_correct_count',
        'grid_incorrect_count', 
        'grid_blank_count',
        'grid_percent_correct',
    ]
   
    def queryset(self, request):
        """Only include non-Solo CompletedTasks. """
        qs = super(CompletedTaskAdmin, self).queryset(request)
        return qs.filter(solo_subject__isnull=True)
    
    def task_link(self, obj):
        return "<a href='%s'>%s</a>" % (
            reverse('admin:mci_task_change', args=(obj.task.id,)), obj.task)
    task_link.allow_tags = True

    def results(self,obj):
        if obj.task.task_type not in ['T', 'G']:
            return ''
        return "<a target='_blank' href='%s'>Results</a>" % reverse(
              'task_results',kwargs={
                  'completed_task_id' : obj.id})
    results.allow_tags = True

    def log(self,obj):
        return "<a href='%s'>Log</a> (<a href='%s'>Export</a>)" % \
                     (reverse('completed_task_log',kwargs={
                        'completed_task_id' : obj.id}),
                      reverse('completed_task_log_export',kwargs={
                        'completed_task_id' : obj.id}))
    log.allow_tags = True

    def contents_txt(self, obj):
        if not obj.task.task_type == 'T':
            return ""
        return "<a href='%s'>Contents as TXT</a>" % \
            reverse( 'completed_task_workspace_text'
                   , kwargs={ 'completed_task_id' : obj.id }
                   )
    contents_txt.allow_tags = True


class SoloCompletedTask(CompletedTask):
    class Meta:
        proxy = True
        verbose_name_plural = "Completed tasks (solo)"

class SoloCompletedTaskAdmin(CompletedTaskAdmin):
    def queryset(self, request):
        """Only include *Solo* CompletedTasks. """
        qs = super(CompletedTaskAdmin, self).queryset(request)
        return qs.filter(solo_subject__isnull=False)
    list_display = [
        'session',
        'subject',
        'task_link',
        'start_time',
        'etherpad_workspace_url',
        'results',
        'log',
    ]
    readonly_fields = [
        'subject',
    ]
    def subject(self, obj):
        if not obj.solo_subject:
            return None
        return "<a href='%s'>%s</a>" % (
            reverse('admin:mci_subject_change', args=(obj.solo_subject.id,)),
            obj.solo_subject)
    subject.allow_tags = True


class CompletedTaskGridItemAdmin(ModelAdminWithPermissionsOnRelatedObjects, ModelAdminWithPermissions):
    list_display = ('session', 'session_group', 'subject', 'task',
                  'task_grid_item','correct_answer','answer')
    list_filter = ('completed_task__session','completed_task__session_group',
                 'completed_task__task', 'task_grid_item')
    fields = [ 'link_task_grid_item'
             , 'link_completed_task'
             , 'link_subject'
             , 'answer'
             ]
    readonly_fields = [ 'link_task_grid_item'
                      , 'link_completed_task'
                      , 'link_subject'
                      , 'answer'
                      ]
    def link_task_grid_item(self, obj):
        return "<a href='%s'>%s</a>" % ( reverse( 'admin:mci_taskgriditem_change'
                                                , args=(obj.task_grid_item.id,)
                                                )
                                       , obj.task_grid_item
                                       )
    link_task_grid_item.allow_tags = True
    link_task_grid_item.short_description = "Task Grid Item"
    def link_completed_task(self, obj):
        return "<a href='%s'>%s</a>" % ( reverse( 'admin:mci_completedtask_change'
                                                , args=(obj.completed_task.id,)
                                                )
                                       , obj.completed_task
                                       )
    link_completed_task.allow_tags = True
    link_completed_task.short_description = "Completed Task"
    def link_subject(self, obj):
        return "<a href='%s'>%s</a>" % ( reverse( 'admin:mci_subject_change'
                                                , args=(obj.subject.id,)
                                                )
                                       , obj.subject
                                       )
    link_subject.allow_tags = True
    link_subject.short_description = "Subject"

    def session(self,obj):
        return obj.completed_task.session

    def session_group(self,obj):
        return obj.completed_task.session_group

    def task(self,obj):
        return obj.completed_task.task

    def correct_answer(self,obj):
        return obj.task_grid_item.correct_answer

class SquaresPiece_Inline(admin.TabularInline):
    model = SquaresPiece
    extra = 0
    fieldsets = [ ('Vertex 0'
                  , { 'fields': [ 'v0_x'
                                , 'v0_y'
                                ]
                    }
                  )
                , ('Vertex 1'
                  , { 'fields': [ 'v1_x'
                                , 'v1_y'
                                ]
                    }
                  )
                , ('Vertex 2'
                  , { 'fields': [ 'v2_x'
                                , 'v2_y'
                                ]
                    }
                  )
                , ('Vertex 3'
                  , { 'fields': [ 'v3_x'
                                , 'v3_y'
                                ]
                    }
                  )
                , ('Vertex 4'
                  , { 'fields': [ 'v4_x'
                                , 'v4_y'
                                ]
                    }
                  )
                , ('Vertex 5'
                  , { 'fields': [ 'v5_x'
                                , 'v5_y'
                                ]
                    }
                  )
                , ('Vertex 6'
                  , { 'fields': [ 'v6_x'
                                , 'v6_y'
                                ]
                    }
                  )
                ,
                ]

class SquaresSetAdmin(PatchedModelAdmin):
    model = SquaresSet
    inlines = [SquaresPiece_Inline]

class SquaresSet_Inline_ForSquaresRoundTemplateAdmin(admin.TabularInline):
    model = SquaresRoundTemplate.squares_sets.through
    verbose_name="Set for use in this Squares round template"
    extra = 0
    sortable_field_name = 'position'    

class SquaresRoundTemplateAdmin(PatchedModelAdmin):
    model = SquaresRoundTemplate
    inlines = [SquaresSet_Inline_ForSquaresRoundTemplateAdmin]
    fields = ['name',]

class ConcentrationCardAdmin(PatchedModelAdmin):
    list_display = ('__unicode__', 'thumbnail')

class ConcentrationRoundTemplateAdmin(PatchedModelAdmin):
    model = ConcentrationRoundTemplate

class ConcentrationCardSetAdmin(PatchedModelAdmin):
    model = ConcentrationCardSet
    fields = ['name', 'cards']


admin.site.register(Text,TextAdmin)
admin.site.register(SessionTemplate, SessionTemplateAdmin)
admin.site.register(SessionBuilder, SessionBuilderAdmin)
admin.site.register(SubjectIdentity, SubjectIdentityAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(SubjectCountry, SubjectCountryAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(TaskGroup, TaskGroupAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(CompletedTask, CompletedTaskAdmin)
admin.site.register(SoloCompletedTask, SoloCompletedTaskAdmin)
admin.site.register(TaskGridItem, TaskGridItemAdmin)
admin.site.register(CompletedTaskGridItem, CompletedTaskGridItemAdmin)
admin.site.register(SquaresSet, SquaresSetAdmin)
admin.site.register(ConcentrationCard, ConcentrationCardAdmin)
admin.site.register(ConcentrationRoundTemplate, ConcentrationRoundTemplateAdmin)
admin.site.register(ConcentrationCardSet, ConcentrationCardSetAdmin)
admin.site.register(SquaresRoundTemplate, SquaresRoundTemplateAdmin)
