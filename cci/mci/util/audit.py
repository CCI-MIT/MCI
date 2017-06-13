from mci.models import EventLog, Subject
from datetime import datetime

__author__ = 'jlicht'

def audit_log(event,request=None,data=None,subject=None,subject_external_id=None,session=None,completed_task=None):
	if not subject:
		try: subject = Subject.objects.get(external_id=subject_external_id)
		except Subject.DoesNotExist: pass
		
	EventLog.objects.create(
      event=event,
	    ip_address=request.META['REMOTE_ADDR'] if request else None,
	    data=data if data is not None else '',
	    subject=subject,
	    session=session if session else subject.session if subject else None,
	    session_group=subject.session_group if subject else None,
			completed_task=completed_task,
      timestamp=datetime.now())
