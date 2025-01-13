import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import services
from .models import Project, WorkItem


def _project(key):
    return Project.objects.filter(key=key).first()


def _plan_payload(project, result):
    return {
        "project": project.key,
        "length_days": result.length_days,
        "finish": result.finish.isoformat(),
        "reserve_days": result.reserve_days,
        "committed_finish": result.committed_finish.isoformat(),
        "critical_path": result.critical_path,
        "near_critical": result.near_critical,
        "tasks": {
            code: {"start": t.start.isoformat(), "finish": t.finish.isoformat(), "slack": t.slack, "critical": t.critical}
            for code, t in sorted(result.tasks.items())
        },
    }


@require_GET
def project_detail(request, key):
    project = _project(key)
    if project is None:
        return JsonResponse({"error": "unknown_project"}, status=404)
    return JsonResponse({
        "key": project.key,
        "name": project.name,
        "status": project.status,
        "team_size": services.team_size(project),
        "counts": services.status_counts(project),
    })


@csrf_exempt
@require_POST
def run_schedule(request, key):
    project = _project(key)
    if project is None:
        return JsonResponse({"error": "unknown_project"}, status=404)
    try:
        result = services.schedule(project)
    except services.ProjectError as exc:
        return JsonResponse({"error": "unschedulable", "detail": str(exc)}, status=422)
    return JsonResponse(_plan_payload(project, result))


@require_GET
def critical_path(request, key):
    project = _project(key)
    if project is None:
        return JsonResponse({"error": "unknown_project"}, status=404)
    try:
        result = services.schedule(project, persist=False)
    except services.ProjectError as exc:
        return JsonResponse({"error": "unschedulable", "detail": str(exc)}, status=422)
    return JsonResponse({"critical_path": result.critical_path, "near_critical": result.near_critical,
                         "length_days": result.length_days})


@csrf_exempt
@require_POST
def add_dependency(request, key):
    project = _project(key)
    if project is None:
        return JsonResponse({"error": "unknown_project"}, status=404)
    try:
        body = json.loads(request.body or b"{}")
        item = WorkItem.objects.get(project=project, code=str(body["item"]))
        needs = WorkItem.objects.get(project=project, code=str(body["depends_on"]))
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "bad_request"}, status=400)
    except WorkItem.DoesNotExist:
        return JsonResponse({"error": "unknown_item"}, status=404)
    try:
        services.add_dependency(item, needs)
    except services.ProjectError as exc:
        return JsonResponse({"error": "rejected", "detail": str(exc)}, status=422)
    return JsonResponse({"item": item.code, "depends_on": needs.code}, status=201)


@require_GET
def sprints(request, key):
    project = _project(key)
    if project is None:
        return JsonResponse({"error": "unknown_project"}, status=404)
    try:
        count = int(request.GET.get("count", "3"))
    except ValueError:
        return JsonResponse({"error": "bad_request"}, status=400)
    windows = services.sprint_windows(project, max(1, min(count, 12)))
    return JsonResponse({"sprints": [{"first": a.isoformat(), "last": b.isoformat()} for a, b in windows]})


