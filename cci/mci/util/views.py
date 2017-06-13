import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from mci.util import audit

@csrf_exempt
def audit_entry(request,subject_external_id):
	if request.method == "POST":
		message = request.POST['message']
		audit.audit_log("Name Change",request=request,subject_external_id=subject_external_id,data=message)
		return HttpResponse(json.dumps({'result' : 'success'}), content_type="application/json")
