# -*- coding: utf-8 -*-
from thumbs import ImageWithThumbsField
from django.db import models
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from markdown import markdown
from djangoratings.fields import RatingField
from djangoratings.models import Vote
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save

class Chapter(models.Model):
    title = models.CharField('title', max_length=90)
    summary = models.TextField('summary', help_text="A short summary of the chapter.")
    summary_html = models.TextField(blank=True, null=True)
    body = models.TextField("body", help_text="You can use markdown formatting. Start with h2 '##' headers as the title is rendered as h1 '#'.")
    body_html = models.TextField(blank=True, null=True)
    mod_date = models.DateTimeField(default=datetime.now)
    pub_date = models.DateTimeField(default=datetime.now)
    index = models.IntegerField(help_text="The chapters position in the book. The higher the later.")
    rating = RatingField(range=5, weight=1, can_change_vote = True, allow_anonymous = False)
    author = models.ForeignKey(User)
    user_created = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    picture = ImageWithThumbsField(upload_to="chapter/", blank=True, null=True, help_text="You don't have to worry about the pictures size. It will automatically resize if over 500 px wide",sizes=((500,100000),(68,68)))
    picture_description = models.CharField('picture description', max_length=255,blank=True, null=True)
    
    class Meta:
        ordering = ['-index']
        get_latest_by = 'pub_date'
    
    def __unicode__(self):
        return self.title
        
    def save(self, *args, **kwargs):             
        self.body_html = markdown(self.body)
        self.summary_html = markdown(self.summary)
        super(Chapter, self).save(*args, **kwargs)
    
    def get_score(self):
        if self.rating.score == 0 or self.rating.votes == 0:
            return self.rating.score
        else:
            return self.rating.score / self.rating.votes
    
    def get_votes_on_chapter(self):
        chapter_type = ContentType.objects.get_for_model(self)
        return Vote.objects.filter(object_id=self.pk, content_type=chapter_type)
    
    def get_number(self):
        chapters = Chapter.objects.filter(visible=True).extra(select={'r': '((100/%s*rating_score/(rating_votes+%s))+100)/2' % (Chapter.rating.range, Chapter.rating.weight)}).order_by('-r')
        i=0
        for chapter in chapters:
            i+=1
            if self==chapter:
                return i
    @models.permalink
    def get_absolute_url(self):
        return ('chapter', [str(self.id)])

class UserChapter(models.Model):
    title = models.CharField('title', max_length=60)
    summary = models.TextField('summary', help_text="A short summary of the chapter.")
    summary_html = models.TextField(blank=True, null=True)
    body = models.TextField("body", help_text="You can use markdown formatting. Start with h2 '##' headers as the title is rendered as h1 '#'.")
    body_html = models.TextField(blank=True, null=True)
    pub_date = models.DateTimeField(default=datetime.now)
    index = models.IntegerField(help_text="The chapters position in the book. The higher the later.")
    author = models.ForeignKey(User)
    picture = ImageWithThumbsField(upload_to="userchapter/", blank=True, null=True, help_text="You don't have to worry about the pictures size. It will automatically resize if over 500 px wide",sizes=((500,100000),(68,68)))
    picture_description = models.CharField('picture description', max_length=255,blank=True, null=True)

    class Meta:
        ordering = ['-index']
        get_latest_by = 'pub_date'
    
    def __unicode__(self):
        return self.title
        
    def save(self, *args, **kwargs):             
        self.body_html = markdown(self.body)
        self.summary_html = markdown(self.summary)
        super(UserChapter, self).save(*args, **kwargs)




def email_when_user_chapter(sender, **kwargs):
    userchapter = kwargs.get('instance')
    created = kwargs.get('created')
    if created:
        from django.core.mail import send_mail
        
        message = '%s have created a user chapter have been created on Winning Without Losing. Check it out on http://winning-without-losing.com/admin/book/userchapter/%s/' % (userchapter.author, userchapter.pk)
        send_mail('New user chapter on Winning Without Losing', message, 'noreply@winning-without-losing.com',
            ['lp@rainmaking.dk'], fail_silently=True)
post_save.connect(email_when_user_chapter, sender=UserChapter)




from django.contrib.syndication.views import Feed

class LatestChapterFeed(Feed):
    title = "Latest chapters on Winning Without Losing"
    link = "/"
    description = "A collaborative book project to discover how to be an ultra successful entrepreneur while living a happy and balanced life"

    def items(self):
        return Chapter.objects.filter(visible=True).order_by('-pub_date')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary
        
    def item_author_name(self, item):
        return item.author
        
    def item_author_link(self, item):
        return '/users/%s' % item.author.username
    
    def item_pubdate(self, item):
        return item.pub_date