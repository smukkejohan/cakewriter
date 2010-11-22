# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from registration.signals import user_activated
from django.db.models.signals import post_save, post_delete
from django.contrib.comments.signals import comment_was_posted
from book.models import Chapter
from datetime import datetime
from django.contrib.comments.models import Comment

import djangoratings.models
import voting.models

from django.db.models import Sum


import logging

class Profile(models.Model):
    user = models.ForeignKey(User, unique=True)
    score = models.IntegerField(default=0)
    level = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.score:
            self.score = 0
        super(Profile, self).save(*args, **kwargs)

CTYPE_CHOICES = (
        ('custom', 'custom'),
        ('rate', 'user rated a chapter for the first time'),
        ('vote', 'user voted on a comment'),    
        ('commentvoted','users comment was voted on by someone else'),
        ('comment', 'user submitted feedback to a chapter'),
    )
    
class ScoreLog(models.Model):
    """
    logs of a users contributions
    """
    
    profile = models.ForeignKey(Profile,)
    chapter = models.ForeignKey(Chapter, null=True, blank=True)
    comment = models.ForeignKey(Comment, null=True, blank=True)
    vote = models.ForeignKey(voting.models.Vote, null=True, blank=True)
    
    description = models.CharField(max_length=200, null =True, blank=True)
    points = models.IntegerField(default=0)
    time = models.DateTimeField(default=datetime.now) 
    ctype = models.CharField(max_length=60, choices=CTYPE_CHOICES, default="custom")   
    
    def save(self, *args, **kwargs):
        super(ScoreLog, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'log: %s %s' % (self.description, self.id)

def update_score(sender, **kwargs):

    instance = kwargs.get('instance')
    
    profile = instance.profile
    logs = ScoreLog.objects.filter(profile=profile)
    profile.score = logs.aggregate(Sum('points'))['points__sum']
    profile.save()
      
post_save.connect(update_score, sender=ScoreLog)
post_delete.connect(update_score, sender=ScoreLog)

def rating_submitted(sender, **kwargs): 
    
    instance = kwargs.get('instance')
    created = kwargs.get('created')
    
    chapter = instance.content_type.get_object_for_this_type(pk=instance.object_id)
        
    try:
        p = instance.user.get_profile()
    except ObjectDoesNotExist:
        p = Profile(user=instance.user)
        p.save()
    
    if created:     
        log = ScoreLog(chapter=chapter, 
            profile=p, 
            points=2, 
            ctype="rate")
        log.save()
    
post_save.connect(rating_submitted, sender=djangoratings.models.Vote)

def vote_submitted(sender, **kwargs): 
    
    instance = kwargs.get('instance')
    
    comment = instance.object
    chapter = comment.content_object
     
    try:
        actor_profile = instance.user.get_profile()
    except ObjectDoesNotExist:
        actor_profile = Profile(user=instance.user)
        actor_profile.save()
    
    try:
        target_profile = comment.user.get_profile()
    except ObjectDoesNotExist:
        target_profile = Profile(user=comment.user)
        target_profile.save()    
    
    try:
        actorLog = ScoreLog.objects.get(ctype='vote', 
            vote=instance)
    except ObjectDoesNotExist:
        actorLog = ScoreLog(ctype='vote', 
        comment=comment, 
        profile=actor_profile,
        vote=instance,
        chapter=chapter)
        
    try:
        targetLog = ScoreLog.objects.get(ctype='commentvoted', 
            vote=instance)
    except ObjectDoesNotExist:
        targetLog = ScoreLog(ctype='commentvoted', 
        comment=comment, 
        profile=target_profile,
        vote=instance,
        chapter=chapter)

    actorLog.time = datetime.now()
    targetLog.time = datetime.now()
        
    if instance.vote == 1:
        actorLog.points = 2
        targetLog.points = 3
    elif instance.vote == -1:
        actorLog.points = 0
        targetLog.points = -1
    
    if target_profile == actor_profile:
        # You dont get points for voting on your own stuff
        actorLog.points = 0
        targetLog.points = 0
           
    targetLog.save()
    actorLog.save()
    
post_save.connect(vote_submitted, sender=voting.models.Vote)


def create_profile(sender, **kwargs):
    """
    Is called on user activation. Creates profile and checks for  pending rating in signals.
    """ 
       
    request = kwargs.get('request')
    user = request.user
    
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
                
        del request.session['pendingrating_chapter']
        del request.session['pendingrating_score']
        
   
user_activated.connect(create_profile)


def user_commented(sender, **kwargs):
    
    request = kwargs.get('request')
    comment = kwargs.get('comment')
    
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

