from usermessage.models import UserMessage
def usermessage(request):
    if not request.user.is_anonymous():
        messages = UserMessage.objects.filter(user=request.user).exclude(category=5).order_by('creation_date').reverse()
        return {'usermessages':messages }
    return {}