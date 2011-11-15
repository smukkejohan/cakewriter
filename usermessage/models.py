# coding: utf-8
from accounts.models import Profile
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
from django.db.models.signals import post_save, pre_save
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site
from registration.signals import user_registered
from django.template import Context
from django.template.loader import get_template

CATEGORY = (
    ('1', 'New comment on your comment'),
    ('2', 'New revision on your revision'),
    ('3', 'New comment on your chapter'),
    ('4', 'New chapters'),
)
class StandardUserMessage(models.Model):
    content = models.TextField()

class UserMessage(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, related_name='user')
    contact =models.ForeignKey(Contact)
    content = models.TextField()
    content_mail = models.TextField()
    creation_date = models.DateTimeField(default=datetime.now())
    category = models.CharField(max_length=1, choices=CATEGORY, default='2')
    chapter = models.ForeignKey(Chapter, blank=True, null=True)
    actor = models.ForeignKey(User, blank=True, null=True, related_name='actor')
    hyperlink = models.CharField(max_length=255, blank=True, null=True)
    hyperlink_usermessage = models.CharField(max_length=255, blank=True, null=True)

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
    
    contentpk = comment.object_pk
    contenttype = comment.content_type
    
    #Email author when comment posted on authors chapter (comment on chapter)
    try:
        chapter_author=comment.content_object.author
    except:
        chapter_author=comment.content_object.created_by
    
    try:
        author_contact = Contact.objects.get(email=chapter_author.email)
    except:
        author_contact = None
    if not chapter_author==comment.user and author_contact:
        hyperlink = 'http://%s%s#c%s' %(Site.objects.get_current(),comment.content_object.get_absolute_url(),comment.id)
        content_mail = "%s with %s points has commented your chapter: [%s](%s), saying: \"%s\"" % (comment.user,
                                                                                         comment.user.get_profile().score,
                                                                                         comment.content_object.title,
                                                                                         hyperlink,
                                                                                         truncate_words(comment.comment,8))
        
        organizer_message = UserMessage(contact=author_contact, 
                                        user=chapter_author,
                                        content_mail=content_mail, 
                                        creation_date=datetime.now(), 
                                        category=3,
                                        hyperlink=hyperlink,
                                        actor=comment.user,
                                        )
        if isinstance(comment.content_object, Chapter):
            organizer_message.chapter = comment.content_object
        if isinstance(comment.content_object, Article):
            organizer_message.chapter = comment.content_object.chapter_related
        organizer_message.save()
        
        hyperlink_usermessage = 'http://%s%s?usermessage=%s#c%s' %(Site.objects.get_current(),
                                                                    comment.content_object.get_absolute_url(),
                                                                    organizer_message.id,
                                                                    comment.id)
        
        content = "%s with %s points has commented your chapter: [%s](%s), saying: \"%s\"" % (comment.user,
                                                                                         comment.user.get_profile().score,
                                                                                         comment.content_object.title,
                                                                                         hyperlink_usermessage,
                                                                                         truncate_words(comment.comment,8))
        organizer_message.hyperlink_usermessage = hyperlink_usermessage
        organizer_message.content = content
        organizer_message.save()
        #email instantly
        plaintext = get_template('email/comment_on_chapter.txt')
        html = get_template('email/comment_on_chapter.html')
        
        c = Context({ 'organizer_message': organizer_message })
        email_plaintext = plaintext.render(c)
        email_html = html.render(c)
        
        msg = EmailMultiAlternatives('Winning Without Losing: comment on your chapter', email_plaintext, 'noreply@winning-without-losing.com', [organizer_message.contact.email])
        msg.attach_alternative(email_html, "text/html")
        msg.send()
    #Email send when someone has commented in a thread where another user has commented (comment on comment)
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
                hyperlink = 'http://%s%s#c%s' %(Site.objects.get_current(),comment.content_object.get_absolute_url(),comment.id)
                content_mail = "%s with %s points has commented the same chapter as you: [%s](%s), saying: \"%s\"" % (comment.user,
                                                                                                 comment.user.get_profile().score,
                                                                                                 comment.content_object.title,
                                                                                                 hyperlink,
                                                                                                 truncate_words(comment.comment,8))
                
                organizer_message = UserMessage(contact=contact, 
                                                user=user,
                                                content_mail=content_mail, 
                                                creation_date=datetime.now(), 
                                                category=1,
                                                hyperlink=hyperlink,
                                                actor=comment.user,
                                                )
                if isinstance(comment.content_object, Chapter):
                    organizer_message.chapter = comment.content_object
                if isinstance(comment.content_object, Article):
                    organizer_message.chapter = comment.content_object.chapter_related
                organizer_message.save()

                hyperlink_usermessage = 'http://%s%s?usermessage=%s#c%s' %(Site.objects.get_current(),
                                                                            comment.content_object.get_absolute_url(),
                                                                            organizer_message.id,
                                                                            comment.id)
                
                content = "%s with %s points has commented the same chapter as you: [%s](%s), saying: \"%s\"" % (comment.user,
                                                                                                 comment.user.get_profile().score,
                                                                                                 comment.content_object.title,
                                                                                                 hyperlink_usermessage, 
                                                                                                 truncate_words(comment.comment,8))
                organizer_message.hyperlink_usermessage = hyperlink_usermessage
                organizer_message.content = content
                organizer_message.save()
                #email instantly
                plaintext = get_template('email/comment_on_comment.txt')
                html = get_template('email/comment_on_comment.html')
                
                c = Context({ 'organizer_message': organizer_message })
                email_plaintext = plaintext.render(c)
                email_html = html.render(c)
                
                msg = EmailMultiAlternatives('Winning Without Losing: Someone has commented the same chapter as you', 
                                            email_plaintext, 'noreply@winning-without-losing.com', 
                                            [organizer_message.contact.email])
                msg.attach_alternative(email_html, "text/html")
                msg.send()

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
                        #Check if person is the author (chapter edited)
                        if userrevision.counter==1:
                            hyperlink = "http://%s%s" % (Site.objects.get_current(),revision.article.get_absolute_url())
                            content_mail = "%s with %s points has edit your chapter: [%s](%s)" % (revision.revision_user,
                                                                                                        revision.revision_user.get_profile().score,
                                                                                                        revision.article.title,
                                                                                                        hyperlink
                                                                                                        )
                            
                            organizer_message = UserMessage(contact=contact, 
                                                            user=user,
                                                            content_mail=content_mail, 
                                                            creation_date=datetime.now(), 
                                                            category=2,
                                                            hyperlink=hyperlink,
                                                            actor=revision.revision_user,
                                                            chapter=revision.article.chapter_related
                                                            )
                            organizer_message.save()
                            hyperlink_usermessage = 'http://%s%s?usermessage=%s' % (Site.objects.get_current(),
                                                                                    revision.article.get_absolute_url(),
                                                                                    organizer_message.id)
                            content = "%s with %s points has edit your chapter: [%s](%s)" % (revision.revision_user,
                                                                                                        revision.revision_user.get_profile().score,
                                                                                                        revision.article.title,
                                                                                                        hyperlink_usermessage 
                                                                                                        )
                            organizer_message.hyperlink_usermessage = hyperlink_usermessage
                            organizer_message.content = content
                            organizer_message.save()
                            
                            #email instantly
                            plaintext = get_template('email/chapter_edited.txt')
                            html = get_template('email/chapter_edited.html')
                            
                            c = Context({ 'organizer_message': organizer_message })
                            email_plaintext = plaintext.render(c)
                            email_html = html.render(c)
                            
                            msg = EmailMultiAlternatives('Winning Without Losing: Your chapter have been edited', 
                                                        email_plaintext, 'noreply@winning-without-losing.com', 
                                                        [organizer_message.contact.email])
                            msg.attach_alternative(email_html, "text/html")
                            msg.send()
                        else:
                            hyperlink = "http://%s%s" % (Site.objects.get_current(),revision.article.get_absolute_url())
                            content_mail = "%s with %s points has edit the same chapter as you: [%s](%s)" % (revision.revision_user,
                                                                                                        revision.revision_user.get_profile().score,
                                                                                                        revision.article.title,
                                                                                                        hyperlink
                                                                                                        )
                            
                            organizer_message = UserMessage(contact=contact, 
                                                            user=user,
                                                            content_mail=content_mail, 
                                                            creation_date=datetime.now(), 
                                                            category=2,
                                                            hyperlink=hyperlink,
                                                            actor=revision.revision_user,
                                                            chapter=revision.article.chapter_related
                                                            )
                            organizer_message.save()
                            hyperlink_usermessage = 'http://%s%s?usermessage=%s' % (Site.objects.get_current(),
                                                                                    revision.article.get_absolute_url(),
                                                                                    organizer_message.id)
                            content = "%s with %s points has edit the same chapter as you: [%s](%s)" % (revision.revision_user,
                                                                                                        revision.revision_user.get_profile().score,
                                                                                                        revision.article.title,
                                                                                                        hyperlink_usermessage
                                                                                                        )
                            organizer_message.hyperlink_usermessage = hyperlink_usermessage
                            organizer_message.content = content
                            organizer_message.save()
                            
                            #email instantly
                            plaintext = get_template('email/edit_on_edit.txt')
                            html = get_template('email/edit_on_edit.html')
                            
                            c = Context({ 'organizer_message': organizer_message })
                            email_plaintext = plaintext.render(c)
                            email_html = html.render(c)
        
                            msg = EmailMultiAlternatives('Winning Without Losing: chapter edited', 
                                                        email_plaintext, 
                                                        'noreply@winning-without-losing.com', 
                                                        [organizer_message.contact.email])
                            msg.attach_alternative(email_html, "text/html")
                            msg.send()

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
                organizer_message = UserMessage(contact=contact, content_mail=content_mail, creation_date=datetime.now(), category=4, chapter=chapter)
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


#---------------POINT EMAILS------------------#
def profile_points(sender, **kwargs):
    profile = kwargs.get('instance')
    created = kwargs.get('created')
    profile_score = profile.score
    try:
        contact = Contact.objects.get(email=profile.user.email, subscriber=True)
    except:
        contact = None
    if created:
        if profile_score>=5 and contact:
            #email instantly
            plaintext = get_template('email/5_points.txt')
            html = get_template('email/5_points.html')
            
            c = Context({'user':profile.user})
            email_plaintext = plaintext.render(c)
            email_html = html.render(c)
            
            msg = EmailMultiAlternatives('Winning Without Losing: exceeded 5 point!', 
                                        email_plaintext, 
                                        'noreply@winning-without-losing.com', 
                                        [profile.user.email])            
            msg.attach_alternative(email_html, "text/html")
            msg.send()
        
        if profile_score>=10 and contact:
            #email instantly
            plaintext = get_template('email/10_points.txt')
            html = get_template('email/10_points.html')
            
            c = Context({'user':profile.user})
            email_plaintext = plaintext.render(c)
            email_html = html.render(c)
            
            msg = EmailMultiAlternatives('Winning Without Losing: exceeded 10 point!', 
                                        email_plaintext, 
                                        'noreply@winning-without-losing.com', 
                                        [profile.user.email])            
            msg.attach_alternative(email_html, "text/html")
            msg.send()
    else:
        try:
            old_profile = Profile.objects.get(pk=profile.pk)
            old_profile_score = old_profile.score
        except:
            old_profile_score = 0
        if old_profile_score<5 and profile_score>=5 and profile_score<10 and contact:
            #email instantly
            plaintext = get_template('email/5_points.txt')
            html = get_template('email/5_points.html')
            
            c = Context({'user':profile.user})
            email_plaintext = plaintext.render(c)
            email_html = html.render(c)
            
            msg = EmailMultiAlternatives('Winning Without Losing: exceeded 5 point!', 
                                        email_plaintext, 
                                        'noreply@winning-without-losing.com', 
                                        [profile.user.email])            
            msg.attach_alternative(email_html, "text/html")
            msg.send()
        
        if old_profile_score<10 and profile_score>=10 and contact:
            #email instantly
            plaintext = get_template('email/10_points.txt')
            html = get_template('email/10_points.html')
            
            c = Context({'user':profile.user})
            email_plaintext = plaintext.render(c)
            email_html = html.render(c)
            
            msg = EmailMultiAlternatives('Winning Without Losing: exceeded 10 point!', 
                                        email_plaintext, 
                                        'noreply@winning-without-losing.com', 
                                        [profile.user.email])            
            msg.attach_alternative(email_html, "text/html")
            msg.send()

pre_save.connect(profile_points, sender=Profile)

#Email send when people registre
def welcome_email(sender, **kwargs):
    request = kwargs.get('request')
    user = kwargs.get('user')
    
    plaintext = get_template('email/welcome.txt')
    html = get_template('email/welcome.html')
    
    c = Context({'user':user})
    email_plaintext = plaintext.render(c)
    email_html = html.render(c)
    
    msg = EmailMultiAlternatives('Winning Without Losing: welcome!', email_plaintext, 'noreply@winning-without-losing.com', [user.email])
    msg.attach_alternative(email_html, "text/html")
    msg.send()    
    
user_registered.connect(welcome_email)