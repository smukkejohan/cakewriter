from django.db import models
from django.contrib.auth.models import User
from emencia.django.newsletter.models import Contact 
from datetime import datetime
from django.utils.text import truncate_words
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.comments.signals import comment_was_posted
from book.models import Chapter
from django.contrib.comments.models import Comment
from simplewiki.models import Article, Revision
from django.db.models import Sum
from markdown import markdown
from django.contrib.sites.models import Site
import os
from django.db.models.signals import post_save
CATEGORY = (
    ('1', 'New comment on your comment'),
    ('2', 'New revision on your revision'),
    ('3', 'New comment on your revision'),
    ('4', 'New chapters'),
)

class UserMessage(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    contact =models.ForeignKey(Contact)
    content = models.TextField()
    content_mail = models.TextField()
    creation_date = models.DateTimeField(default=datetime.now())
    category = models.CharField(max_length=1, choices=CATEGORY, default='2')
    
    def __unicode__(self):
        if self.user:
            return self.user.username
        else:
            return self.contact.email

#--------------------------------AUTOEMAIL----------------------------------#
def user_commented(sender, **kwargs):
    request = kwargs.get('request')
    comment = kwargs.get('comment')
    
    try:
        p = request.user.get_profile()
    except ObjectDoesNotExist:
        p = Profile(user=request.user)
        p.save()
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
            try:
                usercomment = Comment.objects.get(content_type=contenttype, object_pk=contentpk, user=user)
            except MultipleObjectsReturned:
                usercomment = Comment.objects.filter(content_type=contenttype, object_pk=contentpk, user=user)[0]       
            except ObjectDoesNotExist:
                usercomment = None
            if usercomment and user!=comment.user:
                content_mail = "%s with %s points has commented on the same chapter as you: [%s](http://%s%s#c%s), saying: \"%s\"" % (comment.user,
                                                                                                 comment.user.get_profile().score,
                                                                                                 comment.content_object.title,
                                                                                                 Site.objects.get_current(),
                                                                                                 comment.content_object.get_absolute_url(),
                                                                                                 comment.id,
                                                                                                 truncate_words(comment.comment,8))
                
                organizer_message = UserMessage(contact=contact, user=user,content_mail=content_mail, creation_date=datetime.now(), category=1)
                organizer_message.save()
                
                content = "%s with %s points has commented on the same chapter as you: [%s](http://%s%s?usermessage=%s#c%s), saying: \"%s\"" % (comment.user,
                                                                                                 comment.user.get_profile().score,
                                                                                                 comment.content_object.title,
                                                                                                 Site.objects.get_current(),
                                                                                                 comment.content_object.get_absolute_url(),
                                                                                                 organizer_message.id,
                                                                                                 comment.id, 
                                                                                                 truncate_words(comment.comment,8))
                organizer_message.content = content
                organizer_message.save()
comment_was_posted.connect(user_commented)

#Send email to users who have edited chapter when other user has edited the same chapter
def revision_on_revision(sender, **kwargs):
    revision = kwargs.get('instance')
    created = kwargs.get('created')
    revision_user = revision.revision_user
    if created:
        for user in User.objects.all():
            if user!=revision.revision_user:
                try:
                    contact = Contact.objects.get(email=user.email)
                except:
                    contact = None
                if contact:
                    try:
                        userrevision = Revision.objects.get(revision_user=user, article=revision.article)
                    except MultipleObjectsReturned:
                        userrevision = Revision.objects.filter(revision_user=user, article=revision.article)[0]
                    except ObjectDoesNotExist:
                        userrevision = None
                    if userrevision:
                        if userrevision.counter==1:
                            content_mail = "%s with %s points has edit your chapter: [%s](http://%s%s)" % (revision.revision_user,
                                                                                                        revision.revision_user.get_profile().score,
                                                                                                        revision.article.title,
                                                                                                        Site.objects.get_current(),
                                                                                                        revision.article.get_absolute_url()
                                                                                                        )
                                
                            organizer_message = UserMessage(contact=contact, 
                                                            user=user,
                                                            content_mail=content_mail, 
                                                            creation_date=datetime.now(), 
                                                            category=2)
                            organizer_message.save()
                            content = "%s with %s points has edit your chapter: [%s](http://%s%s?usermessage=%s)" % (revision.revision_user,
                                                                                                        revision.revision_user.get_profile().score,
                                                                                                        revision.article.title,
                                                                                                        Site.objects.get_current(),
                                                                                                        revision.article.get_absolute_url(),
                                                                                                        organizer_message.id, 
                                                                                                        )
                            organizer_message.content = content
                            organizer_message.save()
                        else:
                            content_mail = "%s with %s points has edit the same chapter as you: [%s](http://%s%s)" % (revision.revision_user,
                                                                                                        revision.revision_user.get_profile().score,
                                                                                                        revision.article.title,
                                                                                                        Site.objects.get_current(),
                                                                                                        revision.article.get_absolute_url()
                                                                                                        )
                            
                            organizer_message = UserMessage(contact=contact, 
                                                            user=user,
                                                            content_mail=content_mail, 
                                                            creation_date=datetime.now(), 
                                                            category=2)
                            organizer_message.save()
                            content = "%s with %s points has edit the same chapter as you: [%s](http://%s%s?usermessage=%s)" % (revision.revision_user,
                                                                                                        revision.revision_user.get_profile().score,
                                                                                                        revision.article.title,
                                                                                                        Site.objects.get_current(),
                                                                                                        revision.article.get_absolute_url(),
                                                                                                        organizer_message.id, 
                                                                                                        )
                            organizer_message.content = content
                            organizer_message.save()

post_save.connect(revision_on_revision, sender=Revision)
#Send new chapters to everybody that have subscribe (no registration is required)
def email_when_chapter(sender, **kwargs):
    chapter = kwargs.get('instance')
    created = kwargs.get('created')
    if created and chapter.visible:
        for contact in Contact.objects.all():
            if contact.subscriber==True:
                if chapter.author.first_name and chapter.author.last_name:
                    author = chapter.author.first_name+' '+chapter.author.last_name
                else:
                    author = chapter.author.username
                content_mail = "[%s](http://%s%s) by %s: \"%s\"" %(chapter.title,
                                                                           Site.objects.get_current(),
                                                                           chapter.get_absolute_url(),
                                                                           author,
                                                                           truncate_words(chapter.summary,20))
                organizer_message = UserMessage(contact=contact, content_mail=content_mail, creation_date=datetime.now(), category=4)
                if contact.content_object and isinstance(contact.content_object, User):
                    organizer_message.user=contact.content_object
                organizer_message.save()
                organizer_message.content = "[%s](http://%s%s?usermessage=%s) by %s: \"%s\"" %(chapter.title,
                                                                           Site.objects.get_current(),
                                                                           chapter.get_absolute_url(),
                                                                           organizer_message.pk,
                                                                           author,
                                                                           truncate_words(chapter.summary,20))
                organizer_message.save()
post_save.connect(email_when_chapter, sender=Chapter)