# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from usermessage.models import UserMessage
def usermessage_delete(request):
    if request.user:
        if request.POST:
            if 'usermessage' in request.POST:
                usermessage_pk = int(request.POST['usermessage'])
                try:
                    UserMessage.objects.get(user=request.user, pk=usermessage_pk).delete()
                except:
                    error = "some kind of error"
            if 'next' in request.POST:
                last_page = request.POST['next']
                return HttpResponseRedirect(last_page)
            else:
                return HttpResponseRedirect('/')