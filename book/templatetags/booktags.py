from django import template
from django.contrib.contenttypes.models import ContentType
from django.db.models import ObjectDoesNotExist
from book.models import Chapter
from djangoratings.models import Vote

register = template.Library()

def vote_on_chapter_by_user(user, chapter):
    if user:
        c = Chapter.objects.get(pk=chapter.pk)
        chapter_type = ContentType.objects.get_for_model(c)
        try:
            vote = Vote.objects.get(object_id=c.pk, content_type=chapter_type, user=request.user).score
        except:
            vote = 0
    else:
        vote = 0
    return vote
register.tag('vote_on_chapter_by_user', vote_on_chapter_by_user)
