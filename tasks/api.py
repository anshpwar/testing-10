from django.http import Http404, JsonResponse

from .models import Task


def summary(request, ref):
    try:
        obj = Task.objects.get(ref=ref)
    except Task.DoesNotExist:
        raise Http404
    return JsonResponse({"ref": obj.ref, "amount_cents": obj.amount_cents, "status": obj.status})
