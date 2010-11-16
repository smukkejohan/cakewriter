# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from registration.signals import user_activated
from django.db.models.signals import post_save
from book.models import Chapter
from datetime import datetime


class Profile(models.Model):
    user = models.ForeignKey(User, unique=True)
    score = models.IntegerField(default=0)
    level = models.IntegerField(default=0)   

    
class ScoreLog(models.Model):
    """
    logs of a users contributions
    """
    
    profile = models.ForeignKey(Profile)
    description = models.CharField(max_length=60)
    points = models.IntegerField(default=1)
    time = models.DateTimeField(default=datetime.now) 
    #action = models.CharField(max_length=60, default="undefined")
    #target = models.CharField(max_length=60, null=True, blank=True)   
    
    
## handle scores through a bunch of signals 
# vote post save, comment post save, rate post save

def create_profile(sender, user, request, **kw):
    
    try:
        p = user.get_profile()
    except ObjectDoesNotExist:
        p = Profile(user=user)
        p.save()
       
    if request.session['pendingrating_chapter']:
        pending_chapter_id = request.session['pendingrating_chapter']
        pending_score = request.session['pendingrating_score']
        
        chapter = Chapter.objects.get(pk=pending_chapter_id)       
        chapter.rating.add(score=pending_score, user=user, ip_address=request.META['REMOTE_ADDR'])
                   
        log = ScoreLog(profile=p, description='Rated first chapter', points=2)
        log.save()
                
        del request.session['pendingrating_chapter']
        del request.session['pendingrating_score']
        
        logging.debug('session vars deleted')

    
user_activated.connect(create_profile)
