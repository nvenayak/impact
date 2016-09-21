from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse

@login_required
def iPython(request):
    return render(request, 'FermAT_web/iPython.html')

@login_required
def iPython_auth(request):
    # https://developers.shopware.com/blog/2015/03/02/sso-with-nginx-authrequest-module/
    pass
    # if user is authenticated
        # spin up docker container
        # return autheticated
    # else
        # return unautheticated

def check_auth(request):
    if request.user.is_authenticated():
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=401)

def get_username_auth(request):
    # Return the username if authenticated, None if not.
    if request.user.is_authenticated():
        return HttpResponse(request.user.get_username())
    else:
        return HttpResponse('NOT_AUTHORIZED')