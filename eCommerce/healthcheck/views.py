from django.http import JsonResponse

def health_check(request):
    """
    A simple, dependency-free view that returns a 200 OK response.
    This is used by Render for health checks.
    """
    return JsonResponse({"status": "ok"})
