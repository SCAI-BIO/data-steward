from .models import UserToken

def keycloak_auth(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        token = request.data['auth_token']
        if UserToken.objects.filter(token=token).exists():
             return function(request, *args, **kwargs)
        else:
            return HttpResponse("400")
    return wrap
