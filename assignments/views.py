import datetime as dt
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from projects.models import Member, Project, WorkItem

from . import services

ERROR_STATUS = {
    services.PersonOverloaded: (422, "person_overloaded"),
    services.WipLimitReached: (422, "wip_limit"),
}


@csrf_exempt
@require_POST
def assign(request):
    try:
        body = json.loads(request.body or b"{}")
        project = Project.objects.get(key=str(body["project"]))
        item = WorkItem.objects.get(project=project, code=str(body["item"]))
        member = Member.objects.get(project=project, pk=int(body["member"]))
        today = dt.date.fromisoformat(body["today"])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({"error": "bad_request"}, status=400)
    except (Project.DoesNotExist, WorkItem.DoesNotExist, Member.DoesNotExist):
        return JsonResponse({"error": "not_found"}, status=404)
    try:
        assignment = services.assign(item, member, today, int(body.get("hours", 8)))
    except tuple(ERROR_STATUS) as exc:
        status, code = ERROR_STATUS[type(exc)]
        return JsonResponse({"error": code, "detail": str(exc)}, status=status)
    except services.AssignmentError as exc:
        return JsonResponse({"error": "rejected", "detail": str(exc)}, status=400)
    return JsonResponse({"id": assignment.id, "item": item.code, "item_status": item.status}, status=201)


@require_GET
def escalations(request, key):
    project = Project.objects.filter(key=key).first()
    if project is None:
        return JsonResponse({"error": "unknown_project"}, status=404)
    try:
        today = dt.date.fromisoformat(request.GET.get("today", ""))
    except ValueError:
        return JsonResponse({"error": "bad_request"}, status=400)
    due = services.due_for_escalation(project, today)
    return JsonResponse({"due": [{"item": a.item.code, "member": a.member.name, "priority": a.item.priority} for a in due]})
