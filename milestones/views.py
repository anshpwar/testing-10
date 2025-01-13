from django.http import JsonResponse
from django.views.decorators.http import require_GET

from . import services
from .models import Milestone


@require_GET
def milestone_status(request, pk):
    milestone = Milestone.objects.filter(pk=pk).first()
    if milestone is None:
        return JsonResponse({"error": "unknown_milestone"}, status=404)
    try:
        forecast = services.forecast_finish(milestone)
    except services.MilestoneError as exc:
        return JsonResponse({"error": "unscheduled", "detail": str(exc)}, status=409)
    return JsonResponse({
        "name": milestone.name,
        "due_on": milestone.due_on.isoformat(),
        "forecast": forecast.isoformat(),
        "slip_days": services.slip(milestone),
        "status": services.status(milestone),
    })
