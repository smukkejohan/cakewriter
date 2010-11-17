# -*- coding: utf-8 -*-

from django.db import models
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from markdown2 import markdown
from djangoratings.fields import RatingField

class Chapter(models.Model):
    title = models.CharField('title', max_length=90)
    summary = models.TextField('summary', help_text="A short summary of the chapter.")
    summary_html = models.TextField()
    body = models.TextField("body", help_text="You can use markdown formatting. Start with h2 '##' headers as the title is rendered as h1 '#'.")
    body_html = models.TextField()
    mod_date = models.DateTimeField(default=datetime.now)
    pub_date = models.DateTimeField(default=datetime.now)
    index = models.IntegerField(help_text="The chapters position in the book. The higher the later.")
    rating = RatingField(range=5, can_change_vote = True, allow_anonymous = False)
    
    class Meta:
        ordering = ['-index']
        get_latest_by = 'pub_date'
    
    def __unicode__(self):
        return self.title
        
    def save(self):
        self.body_html = markdown(self.body)
        self.summary_html = markdown(self.summary)
        self.mod_date = datetime.now()
        super(Chapter, self).save()
        
    @models.permalink
    def get_absolute_url(self):
        return ('chapter', [str(self.id)])

