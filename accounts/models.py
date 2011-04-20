# -*- coding: utf-8 -*-
from django.utils.text import truncate_words
from django.db import models
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from registration.signals import user_activated
from django.db.models.signals import post_save, post_delete
from django.contrib.comments.signals import comment_was_posted
from book.models import Chapter
from datetime import datetime
from django.contrib.comments.models import Comment
from simplewiki.models import Article
import djangoratings.models
import voting.models
from html_mailer.models import Message, Organizer
from django.db.models import Sum
from emencia.django.newsletter.models import Contact
from markdown import markdown
from django.contrib.sites.models import Site
import logging
from simplewiki.models import Revision

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
        ('wikicomment', 'user submitted feedbact to a wikichapter'),
        ('editedarticle', 'user edited an article'),
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
            points=1, 
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
        actorLog.points = 1
        targetLog.points = 2
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
    user = kwargs.get('user')
    
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

#10 points when user EDIT ARTICLE

def user_edited_article(sender, **kwargs):
    revision = kwargs.get('instance')
    try:
        p = revision.revision_user.get_profile()
    except ObjectDoesNotExist:
        p = Profile(user=revision.revision_user)
        p.save()
        
    log = ScoreLog(chapter=revision.article.chapter_related, 
                profile=p, 
                description='user edited an article', 
                points=10, 
                ctype="editedarticle")
    log.save()
post_save.connect(user_edited_article, sender=Revision)

def user_commented(sender, **kwargs):
    
    request = kwargs.get('request')
    comment = kwargs.get('comment')
    
    try:
        p = request.user.get_profile()
    except ObjectDoesNotExist:
        p = Profile(user=request.user)
        p.save()
    chap = Chapter.objects.all()
    for chapter in chap:
        if comment.content_object==chapter:
            log = ScoreLog(comment=comment, 
                chapter=comment.content_object, 
                profile=p, 
                description='Submitted feedback to a chapter', 
                points=3, 
                ctype="comment")
    '''
        else:
            log = ScoreLog(comment=comment, 
                chapter=comment.content_object.chapter_related, 
                profile=p, 
                description='Submitted feedback to a wikichapter', 
                points=3, 
                ctype="wikicomment")
    '''
    art = Article.objects.all()
    for article in art:
        if comment.content_object==article:
            log = ScoreLog(comment=comment, 
                chapter=comment.content_object.chapter_related, 
                profile=p, 
                description='Submitted feedback to a wikichapter', 
                points=3, 
                ctype="wikicomment")
    
    log.save()
    
    #--------------------------------AUTOEMAIL----------------------------------#
    
    #Email send when someone has commented in a thread where another user has commented
    contentpk = comment.object_pk
    contenttype = comment.content_type
    users = User.objects.all()
    for user in users:
        try:
            contact = Contact.objects.get(email=user.email)
        except:
            contact = None
        if contact:
            if contact.subscriber==True:
                try:
                    usercomment = Comment.objects.get(content_type=contenttype, object_pk=contentpk, user=user)
                except MultipleObjectsReturned:
                    usercomment = Comment.objects.filter(content_type=contenttype, object_pk=contentpk, user=user)[0]       
                except ObjectDoesNotExist:
                    usercomment = None
                if usercomment and user!=comment.user:
                    message_text = "%s with %s points has commented on the same chapter as you: [%s](http://%s%s#c%s), saying: \"%s\"" % (comment.user,
                                                                                                     comment.user.get_profile().score,
                                                                                                     comment.content_object.title,
                                                                                                     Site.objects.get_current(),
                                                                                                     comment.content_object.get_absolute_url(),
                                                                                                     comment.id,
                                                                                                     truncate_words(comment.comment,8))
                    organizer_message = Organizer(user=contact, message=message_text, when_added=datetime.now(), category=1)
                    organizer_message.save()

comment_was_posted.connect(user_commented)

#Send email to users who have edited chapter when other user has edited the same chapter
def revision_on_revision(sender, **kwargs):
    revision = kwargs.get('instance')

#Send new chapters to everybody that have subscribe (no registration is required)
def email_when_chapter(sender, **kwargs):
    chapter = kwargs.get('instance')
    created = kwargs.get('created')
    if created and chapter.visible:
        for user in Contact.objects.all():
            if user.subscriber==True:
                if chapter.author.first_name and chapter.author.last_name:
                    author = chapter.author.first_name+' '+chapter.author.last_name
                else:
                    author = chapter.author.username
                message = "[%s](http://%s%s) by %s: \"%s\"" %(chapter.title,
                                                                           Site.objects.get_current(),
                                                                           chapter.get_absolute_url(),
                                                                           author,
                                                                           truncate_words(chapter.summary,20))
                organizer_message = Organizer(user=user, message=message, when_added=datetime.now(), category=4)
                organizer_message.save()
post_save.connect(email_when_chapter, sender=Chapter)
#--------------------------------EMAILCONTACTS----------------------------------#

#Email-contacts created when user is saved
from django.db.models import signals
from emencia.django.newsletter.models import Contact
from emencia.django.newsletter.models import MailingList

def create_contact(sender, **kwargs):
    user = kwargs.get('instance')
    created = kwargs.get('created')
    if created:
        #contact, created = Contact.objects.get_or_create(email=user.email,
        #                                                 defaults={'first_name':user.username,
        #                                                           'last_name': '',
        #                                                           'content_object':user})
        try:
            contact = Contact.objects.get(email=user.email)
            if contact:
                if contact.content_object==None:
                    contact.content_object = user
                    contact.first_name = user.username
                    contact.save()
        except ObjectDoesNotExist:
            contact_final = Contact.objects.create(email=user.email, first_name=user.username, content_object=user)
            contact_final.save()
        #all users is made ready for the ManytoManyField
        subscribers=[]
        contacts = Contact.objects.all()
        for e in contacts:
            subscribers.append(e)
        #Create Maillist with all users
        mailinglists = MailingList.objects.filter(name='All users')
        if mailinglists.count() > 0:
            mailinglist = mailinglists[0]
            mpk = mailinglist.pk
            new_mailing = MailingList(pk=mpk,
                                      name='All users',
                                      description='Mailinglist with all users',
                                      creation_date=mailinglist.creation_date,
                                      modification_date=mailinglist.modification_date,)
        else: 
            new_mailing = MailingList(name='All users',
                                      description='Mailinglist with all users')
        new_mailing.save()
        new_mailing.subscribers.add(*subscribers)
        new_mailing.save()    
post_save.connect(create_contact, sender=User)