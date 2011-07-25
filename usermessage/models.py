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

CATEGORY = (
    ('1', 'New comment on your comment'),
    ('2', 'New revision on your revision'),
    ('3', 'New comment on your revision'),
    ('4', 'New chapters'),
)
class StandardUserMessage(models.Model):
    content = models.TextField()

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
                #email instantly
                email_message = 'Hi %s, a comment was posted on the same chapter as you have commented:\n\n%s'%(organizer_message.user,organizer_message.content)
                msg = EmailMultiAlternatives('Winning Without Losing: One have commented on the same chapter as you', email_message, 'noreply@winning-without-losing.com', [organizer_message.contact.email])
                email_html_message = '<div style="width:100%%; height:100%%; margin:0px; background-color:#d3d8d;"><div style="background-color:#d3d8dd;"><div style="padding:50px 0px 50px 0px;"><div style="margin:0px auto 0px auto; background-color:#FFF; width:600px; padding-bottom:30px;font-family: Helvetica, Verdana, Arial, sans-serif;-moz-box-shadow:  0px 0px 50px 0px #3d3d3d; -webkit-box-shadow: 0px 0px 50px 0px #3d3d3d; box-shadow: 0px 0px 50px 0px #3d3d3d;"><div style="height:50px;background-color:#01a3d4; padding:40px 0px 40px 30px; font-size:20px; font-weight: bold; font-size: 50px; color:#FFF; text-shadow: #000 0px -1px 0px;">Updates from WWL</div><div style="padding:50px 50px 0px 50px; color:#565454;">Hi %s, a comment was posted on the same chapter as you have commented:<br /><br />\n%s\n<br /><p>Winning Without Losing</p><p>www.winning-without-losing.com</p><img src="http://m.winning-without-losing.com/img/logo.jpg" /><p>if you want to unsubscribe from these update <a href="http://%s/newsletters/mailing/unsubscribe/">click here</a></p></div></div></div></div></div>' % (organizer_message.user,markdown(organizer_message.content),Site.objects.get_current())
                msg.attach_alternative(email_html_message, "text/html")
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
                        #Check if person is the author
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
                            
                            #email instantly
                            email_message = 'Hi %s, your chapter have been edited:\n\n%s'%(organizer_message.user,organizer_message.content)
                            msg = EmailMultiAlternatives('Winning Without Losing: Your chapter have been edited', email_message, 'noreply@winning-without-losing.com', [organizer_message.contact.email])
                            email_html_message = '<div style="width:100%%; height:100%%; margin:0px; background-color:#d3d8d;"><div style="background-color:#d3d8dd;"><div style="padding:50px 0px 50px 0px;"><div style="margin:0px auto 0px auto; background-color:#FFF; width:600px; padding-bottom:30px;font-family: Helvetica, Verdana, Arial, sans-serif;-moz-box-shadow:  0px 0px 50px 0px #3d3d3d; -webkit-box-shadow: 0px 0px 50px 0px #3d3d3d; box-shadow: 0px 0px 50px 0px #3d3d3d;"><div style="height:50px;background-color:#01a3d4; padding:40px 0px 40px 30px; font-size:20px; font-weight: bold; font-size: 50px; color:#FFF; text-shadow: #000 0px -1px 0px;">Updates from WWL</div><div style="padding:50px 50px 0px 50px; color:#565454;">Hi %s, your chapter have been edited:<br /><br />\n%s\n<br /><p>Winning Without Losing</p><p>www.winning-without-losing.com</p><img src="http://m.winning-without-losing.com/img/logo.jpg" /><p>if you want to unsubscribe from these update <a href="http://%s/newsletters/mailing/unsubscribe/">click here</a></p></div></div></div></div></div>' % (organizer_message.user,markdown(organizer_message.content),Site.objects.get_current())
                            msg.attach_alternative(email_html_message, "text/html")
                            msg.send()
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
                            
                            #email instantly
                            email_message = 'Hi %s, a chapter you have edited have been edited:\n\n%s'%(organizer_message.user,organizer_message.content)
                            msg = EmailMultiAlternatives('Winning Without Losing: chapter edited', email_message, 'noreply@winning-without-losing.com', [organizer_message.contact.email])
                            email_html_message = '<div style="width:100%%; height:100%%; margin:0px; background-color:#d3d8d;"><div style="background-color:#d3d8dd;"><div style="padding:50px 0px 50px 0px;"><div style="margin:0px auto 0px auto; background-color:#FFF; width:600px; padding-bottom:30px;font-family: Helvetica, Verdana, Arial, sans-serif;-moz-box-shadow:  0px 0px 50px 0px #3d3d3d; -webkit-box-shadow: 0px 0px 50px 0px #3d3d3d; box-shadow: 0px 0px 50px 0px #3d3d3d;"><div style="height:50px;background-color:#01a3d4; padding:40px 0px 40px 30px; font-size:20px; font-weight: bold; font-size: 50px; color:#FFF; text-shadow: #000 0px -1px 0px;">Updates from WWL</div><div style="padding:50px 50px 0px 50px; color:#565454;">Hi %s, a chapter you have edited have been edited:<br /><br />\n%s\n<br /><p>Winning Without Losing</p><p>www.winning-without-losing.com</p><img src="http://m.winning-without-losing.com/img/logo.jpg" /><p>if you want to unsubscribe from these update <a href="http://%s/newsletters/mailing/unsubscribe/">click here</a></p></div></div></div></div></div>' % (organizer_message.user,markdown(organizer_message.content),Site.objects.get_current())
                            msg.attach_alternative(email_html_message, "text/html")
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


#for points
def profile_points_10(sender, **kwargs):
    profile = kwargs.get('instance')
    created = kwargs.get('created')
    profile_score = profile.score
    try:
        contact = Contact.objects.get(email=profile.user.email, subscriber=True)
    except:
        contact = None
    if created:
        if profile_score>=10 and contact:
            #email instantly
            email_message = '''
Hi %s! 

Congratulations, you got 15 bi-winning points! You are now officially part of the project and will be credited as a co-creator of our first book!

Now, remember to fill out your profile form, so we know exactly who to give credit to. You can also link it to your website or Facebook account to make it easier for people who like what you write to contact you.

And be sure that we will send you a copy of the book, wherever you are!

Have a nice day!

The Winning Without Losing team.
www.winning-without-losing.com
''' % profile.user
            msg = EmailMultiAlternatives('Winning Without Losing: exceeded 15 point!', email_message, 'noreply@winning-without-losing.com', [profile.user.email])
            email_html_message = '''
<div style="width:100%%; height:100%%; margin:0px; background-color:#d3d8d;"><div style="background-color:#d3d8dd;"><div style="padding:50px 0px 50px 0px;"><div style="margin:0px auto 0px auto; background-color:#FFF; width:600px; padding-bottom:30px;font-family: Helvetica, Verdana, Arial, sans-serif;-moz-box-shadow:  0px 0px 50px 0px #3d3d3d; -webkit-box-shadow: 0px 0px 50px 0px #3d3d3d; box-shadow: 0px 0px 50px 0px #3d3d3d;"><div style="height:50px;background-color:#01a3d4; padding:40px 0px 40px 30px; font-size:20px; font-weight: bold; font-size: 50px; color:#FFF; text-shadow: #000 0px -1px 0px;">Updates from WWL</div><div style="padding:50px 50px 0px 50px; color:#565454;">

<p>Hi %s!</p>

<p>Congratulations, you got 15 bi-winning points! You are now officially part of the project and will be credited as a co-creator of our first book!</p>

<p>Now, remember to fill out your <a href="http://%s/account/edit/">profile form</a>, so we know exactly who to give credit to. You can also link it to your website or Facebook account to make it easier for people who like what you write to contact you.</p>

<p>And be sure that we will send you a copy of the book, wherever you are!</p>

<p>Have a nice day!</p>

<p>The Winning Without Losing team</p>
<p>www.winning-without-losing.com</p>
<img src="http://m.winning-without-losing.com/img/logo.jpg" /><p>if you want to unsubscribe from these update <a href="http://%s/newsletters/mailing/unsubscribe/">click here</a></p>

</div></div></div></div></div>
''' % (profile.user,Site.objects.get_current(),Site.objects.get_current())
            
            msg.attach_alternative(email_html_message, "text/html")
            msg.send()
    else:
        try:
            old_profile = Profile.objects.get(pk=profile.pk)
            old_profile_score = old_profile.score
        except:
            old_profile_score = 0
        if old_profile_score<10 and profile_score>=10 and contact:
            #email instantly
            email_message = '''
Hi %s! 

Congratulations, you got 15 bi-winning points! You are now officially part of the project and will be credited as a co-creator of our first book!

Now, remember to fill out your profile form, so we know exactly who to give credit to. You can also link it to your website or Facebook account to make it easier for people who like what you write to contact you.

And be sure that we will send you a copy of the book, wherever you are!

Have a nice day!

The Winning Without Losing team.
www.winning-without-losing.com
''' % profile.user
            msg = EmailMultiAlternatives('Winning Without Losing: exceeded 15 point!', email_message, 'noreply@winning-without-losing.com', [profile.user.email])
            email_html_message = '''
<div style="width:100%%; height:100%%; margin:0px; background-color:#d3d8d;"><div style="background-color:#d3d8dd;"><div style="padding:50px 0px 50px 0px;"><div style="margin:0px auto 0px auto; background-color:#FFF; width:600px; padding-bottom:30px;font-family: Helvetica, Verdana, Arial, sans-serif;-moz-box-shadow:  0px 0px 50px 0px #3d3d3d; -webkit-box-shadow: 0px 0px 50px 0px #3d3d3d; box-shadow: 0px 0px 50px 0px #3d3d3d;"><div style="height:50px;background-color:#01a3d4; padding:40px 0px 40px 30px; font-size:20px; font-weight: bold; font-size: 50px; color:#FFF; text-shadow: #000 0px -1px 0px;">Updates from WWL</div><div style="padding:50px 50px 0px 50px; color:#565454;">

<p>Hi %s!</p>

<p>Congratulations, you got 15 bi-winning points! You are now officially part of the project and will be credited as a co-creator of our first book!</p>

<p>Now, remember to fill out your <a href="http://%s/account/edit/">profile form</a>, so we know exactly who to give credit to. You can also link it to your website or Facebook account to make it easier for people who like what you write to contact you.</p>

<p>And be sure that we will send you a copy of the book, wherever you are!</p>

<p>Have a nice day!</p>

<p>The Winning Without Losing team</p>
<p>www.winning-without-losing.com</p>
<img src="http://m.winning-without-losing.com/img/logo.jpg" /><p>if you want to unsubscribe from these update <a href="http://%s/newsletters/mailing/unsubscribe/">click here</a></p>

</div></div></div></div></div>
''' % (profile.user,Site.objects.get_current(),Site.objects.get_current())
            msg.attach_alternative(email_html_message, "text/html")
            msg.send()
pre_save.connect(profile_points_10, sender=Profile)

#Email send when people registre
def registration_mail(sender, **kwargs):
    request = kwargs.get('request')
    user = kwargs.get('user')
    email_message = '''
Welcome to Winning Without Losing, %s! Thank you for joining!

It is a collaborative book project, so it is important to give us feedback: your participation will determine which authors and chapters are going to be included in the final book!
If you want to learn a bit more about how chapters and authors get selected, you can check our “How It Works” section! 

You will be granted bi-winning points according on your activity on the website:
20 points if you submit a new chapter;
10 points is you edit a chapter;
3 points if you comment a chapter;
1 point if you rate a chapter;

Every active participant will be credited in the book as a co-creator. You just need to obtain 15 points for this!

You can visit http://%s/book/ to read, rate, comment and edit chapters.

Have a nice day!

The Winning Without Losing team.
www.winning-without-losing.com

if you want to unsubscribe from these update visit: http://%s/newsletters/mailing/unsubscribe/
''' % (user,Site.objects.get_current(),Site.objects.get_current())
    msg = EmailMultiAlternatives('Winning Without Losing: thank you for joining!', email_message, 'noreply@winning-without-losing.com', [user.email])
    email_html_message = '''
<div style="width:100%%; height:100%%; margin:0px; background-color:#d3d8d;"><div style="background-color:#d3d8dd;"><div style="padding:50px 0px 50px 0px;"><div style="margin:0px auto 0px auto; background-color:#FFF; width:600px; padding-bottom:30px;font-family: Helvetica, Verdana, Arial, sans-serif;-moz-box-shadow:  0px 0px 50px 0px #3d3d3d; -webkit-box-shadow: 0px 0px 50px 0px #3d3d3d; box-shadow: 0px 0px 50px 0px #3d3d3d;"><div style="height:50px;background-color:#01a3d4; padding:40px 0px 40px 30px; font-size:20px; font-weight: bold; font-size: 50px; color:#FFF; text-shadow: #000 0px -1px 0px;">Updates from WWL</div><div style="padding:50px 50px 0px 50px; color:#565454;">

<p>Welcome to Winning Without Losing, %s! Thank you for joining!</p>

<p>It is a collaborative book project, so it is important to give us feedback: your participation will determine which authors and chapters are going to be included in the final book!
If you want to learn a bit more about how chapters and authors get selected, you can check our “How It Works” section!</p>

<p>You will be granted bi-winning points according on your activity on the website:</p>
<ul>
<li>20 points if you submit a new chapter;</li>
<li>10 points is you edit a chapter;</li>
<li>3 points if you comment a chapter;</li>
<li>1 point if you rate a chapter;</li>
</ul>
<p>Every active participant will be credited in the book as a co-creator. You just need to obtain 15 points for this!</p>

<p>You can go <a href="http://%s/book/">here</a> to read, rate, comment and edit chapters.</p>

<p>Have a nice day!</p>

<p>The Winning Without Losing team</p>
<p>www.winning-without-losing.com</p>
<img src="http://m.winning-without-losing.com/img/logo.jpg" /><p>if you want to unsubscribe from these update <a href="http://%s/newsletters/mailing/unsubscribe/">click here</a></p>

</div></div></div></div></div>
''' % (user,Site.objects.get_current(),Site.objects.get_current())
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()    
    
user_registered.connect(registration_mail)