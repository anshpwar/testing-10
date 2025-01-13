import datetime as dt
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from projects.models import Member, WorkItem

from . import services

ERROR_STATUS = {
    services.DayFull: (422, "day_full"),
    services.WeekLocked: (423, "week_locked"),
}


@csrf_exempt
@require_POST
def log(request):
    try:
        body = json.loads(request.body or b"{}")
        member = Member.objects.get(pk=int(body["member"]))
        item = WorkItem.objects.get(project=member.project, code=str(body["item"]))
        worked_on = dt.date.fromisoformat(body["worked_on"])
        today = dt.date.fromisoformat(body["today"])
        minutes = int(body["minutes"])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({"error": "bad_request"}, status=400)
    except (Member.DoesNotExist, WorkItem.DoesNotExist):
        return JsonResponse({"error": "not_found"}, status=404)
    try:
        entry = services.log_time(member, item, worked_on, minutes, today, str(body.get("note", ""))[:80])
    except tuple(ERROR_STATUS) as exc:
        status, code = ERROR_STATUS[type(exc)]
        return JsonResponse({"error": code, "detail": str(exc)}, status=status)
    except services.TimesheetError as exc:
        return JsonResponse({"error": "rejected", "detail": str(exc)}, status=400)
    return JsonResponse({"id": entry.id, "minutes": entry.minutes}, status=201)


@require_GET
def week(request, member_id, day):
    member = Member.objects.filter(pk=member_id).first()
    if member is None:
        return JsonResponse({"error": "unknown_member"}, status=404)
    try:
        when = dt.date.fromisoformat(day)
    except ValueError:
        return JsonResponse({"error": "bad_request"}, status=400)
    summary = services.week_summary(member, when)
    summary["week_start"] = summary["week_start"].isoformat()
    return JsonResponse(summary)
