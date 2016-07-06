from ci_dashboard.models import UserToken


class TokenAuthMiddleware(object):
    @staticmethod
    def process_request(request):
        token = request.META.get('HTTP_TOKEN')
        if not token:
            return
        try:
            request.user = UserToken.objects.get(token=token).user
        except UserToken.DoesNotExist:
            pass
