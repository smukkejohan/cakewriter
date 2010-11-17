# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from registration.signals import user_activated
from django.db.models.signals import post_save
from django.contrib.comments.signals import comment_was_posted
from book.models import Chapter
from datetime import datetime
from django.contrib.comments.models import Comment

from django.db.models import Sum


import logging

class Profile(models.Model):
    user = models.ForeignKey(User, unique=True)
    score = models.IntegerField(default=0)
    level = models.IntegerField(default=0)

CTYPE_CHOICES = (
        ('custom', 'custom'),
        ('rate', 'user rated a chapter for the first time'),
        ('voteup', 'user voted a comment up'),
        ('votedown', 'user voted a comment down'),
        ('voteclear', 'user cleared a vote'),
        ('comment', 'user submitted feedback to a chapter'),
    )
    
class ScoreLog(models.Model):
    """
    logs of a users contributions
    """
    
    profile = models.ForeignKey(Profile)
    chapter = models.ForeignKey(Chapter, null=True, blank=True)
    comment = models.ForeignKey(Comment, null=True, blank=True)
    description = models.CharField(max_length=200, null =True, blank=True)
    points = models.IntegerField(default=0)
    time = models.DateTimeField(default=datetime.now) 
    ctype = models.CharField(max_length=60, choices=CTYPE_CHOICES, default="custom")   
    
    def save(self, *args, **kwargs):
        super(ScoreLog, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'log: %s %s' % (self.description, self.id)


def update_score(sender, instance, created, using, **kwargs): 
    profile = instance.profile
    logs = ScoreLog.objects.filter(profile=profile)
    profile.score = logs.aggregate(Sum('points'))['points__sum']
    profile.save()
    print 'score updated'
      
post_save.connect(update_score, sender=ScoreLog)



def create_profile(sender, user, request, **kwargs):
    """
    Is called on user activation. Creates profile and checks for  pending rating in signals.
    """ 
    
    try:
        p = user.get_profile()
    except ObjectDoesNotExist:
        p = Profile(user=user)
        p.save()
       
    if request.session.get('pendingrating_chapter'):
        pending_chapter_id = request.session['pendingrating_chapter']
        pending_score = request.session['pendingrating_score']
        
        chapter = Chapter.objects.get(pk=pending_chapter_id)       
        chapter.rating.add(score=pending_score, 
            user=user, 
            ip_address=request.META['REMOTE_ADDR'])
                   
        log = ScoreLog(profile=p, description='Rated first chapter', points=2, ctype="rate", chapter=chapter)
        log.save()
                
        del request.session['pendingrating_chapter']
        del request.session['pendingrating_score']
        
   
user_activated.connect(create_profile)


def user_commented(sender, comment, request, **kwargs):
    try:
        p = request.user.get_profile()
    except ObjectDoesNotExist:
        p = Profile(user=request.user)
        p.save()
    
    log = ScoreLog(comment=comment, 
        chapter=comment.content_object, 
        profile=p, 
        description='Submitted feedback to a chapter', 
        points=4, 
        ctype="comment")
    log.save()
    
    
comment_was_posted.connect(user_commented)

