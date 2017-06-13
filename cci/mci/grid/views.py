import logging
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import redis
from mci.models import CompletedTask, CompletedTaskGridItem, Subject
from mci.util import audit
from settings import MCI_REDIS_PORT, MCI_REDIS_SERVER

_log = logging.getLogger('cci')

# Assumes that no tasks will last longer than an hour
REDIS_KEY_EXPIRATION_TIME = 3600

def _get_redis():
	return redis.Redis(host=MCI_REDIS_SERVER,port=MCI_REDIS_PORT)

def _completed_task_key(completed_task_id):
	return "CompletedTask-" + completed_task_id

def _grid_items_focus_key(completed_task_id):
	return "CompletedTaskFocus-" + completed_task_id

@csrf_exempt
def grid_items(request,completed_task_id):
	""""Return all the grid items associated with a task that's being worked on"""
	r, result = _get_redis(), None
	try:
		result = r.get(_completed_task_key(completed_task_id))
	except Exception:
		_log.error("Error getting grid item status in Redis")

	# Get the current status of all the grid items from the database if not in the cache
	if not result:
		try:
			completed_task = CompletedTask.objects.get(pk=completed_task_id)
			completed_grid_items = completed_task.completedtaskgriditem_set.all()
		except CompletedTask.DoesNotExist:
			return HttpResponse(json.dumps({'result' : 0}), content_type="application/json")

		response_data = { 'data' : {}, 'correct' : {}, 'result' : 1, 'focus' : {} }
		for x in list(completed_grid_items):
			response_data['data'][x.task_grid_item.id] = x.answer # Do we need to html escape here?
			response_data['correct'][x.task_grid_item.id] = x.correct()
		result = json.dumps(response_data)
		try:
			r.set(_completed_task_key(completed_task_id),result)
			r.expire(_completed_task_key(completed_task_id),REDIS_KEY_EXPIRATION_TIME)
		except Exception:
			_log.error("Error setting grid item status in Redis")

	try:
		# Update the cache with the grid item on which the requesting user is focused (if any)
		if 'focus' in request.POST and 'subject_external_id' in request.POST:
			r.hset(_grid_items_focus_key(completed_task_id),request.POST['subject_external_id'],request.POST['focus'])
			r.expire(_grid_items_focus_key(completed_task_id),REDIS_KEY_EXPIRATION_TIME)

		# Add to the response the grid items that are focused on
		response_focus_data = json.loads(result)
		response_focus_data['focus'] = r.hgetall(_grid_items_focus_key(completed_task_id))
		result = json.dumps(response_focus_data)

	except Exception:
		_log.error("Error updating focus data in redis")

	return HttpResponse(result, content_type="application/json")

@csrf_exempt
def save_grid_item(request):
  """"
  Create or update an answer for a specific grid item
  """
  if request.method == "POST":

    # Make sure request body is valid
    if False in [c in request.POST for c in ['subject_external_id','completed_task_id', 'task_grid_item_id', 'answer']]:
      return HttpResponse(json.dumps({'result' : 'error'}), content_type="application/json")
    # Make sure this Subject can edit
    subject = Subject.objects.get(external_id = request.POST['subject_external_id'])
    ct = CompletedTask.objects.get(pk=request.POST['completed_task_id'])
    if not subject.is_scribe_or_scribe_disabled(ct):
      return HttpResponse(json.dumps({ 'result' : 'error' 
                                     , 'reason' : 'user is not the scribe' 
                                     }), content_type="application/json")
    try:
      previous_answer = None
      try:
        completed_task_grid_item = CompletedTaskGridItem.objects.get( completed_task__pk = request.POST['completed_task_id']
                                                                    , task_grid_item__pk = request.POST['task_grid_item_id']
                                                                    )
        previous_answer = completed_task_grid_item.answer
      except CompletedTaskGridItem.DoesNotExist:
        completed_task_grid_item = CompletedTaskGridItem( completed_task_id = request.POST['completed_task_id']
                                                        , task_grid_item_id = request.POST['task_grid_item_id']
                                                        )
      completed_task_grid_item.answer = request.POST['answer']
      if previous_answer <> completed_task_grid_item.answer:
        try:
          completed_task_grid_item.subject = subject
        except Subject.DoesNotExist: pass
        r = _get_redis()
        try:
          r.delete(_completed_task_key(request.POST['completed_task_id']))
        except Exception:
          _log.error("Error clearing grid item status in Redis")
        completed_task_grid_item.save()
        audit.audit_log( "Edit Grid"
                       , data="[%s,%s] : %s" % ( completed_task_grid_item.task_grid_item.row
                                               , completed_task_grid_item.task_grid_item.column
                                               , completed_task_grid_item.answer
                                               )
                       , request=request
                       , subject=completed_task_grid_item.subject
                       , completed_task=completed_task_grid_item.completed_task
                       )
    except CompletedTask.DoesNotExist:
      return HttpResponse(json.dumps({'result' : 'error'}), content_type="application/json")
    return HttpResponse(json.dumps({'result' : 'success'}), content_type="application/json")
  else:
    return HttpResponse(json.dumps({'result' : 'error'}), content_type="application/json")
