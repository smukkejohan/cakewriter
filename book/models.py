# -*- coding: utf-8 -*-

from django.db import models
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
#from markdown2 import markdown
from djangoratings import RatingField

class Chapter(models.Model):
    title = models.CharField('overskrift', max_length=200)
    body = models.TextField("brødtekst", help_text="Brug markdown formatering")
    body_html = models.TextField()
    mod_date = models.DateTimeField(default=datetime.now)
    pub_date = models.DateTimeField(default=datetime.now)
    index = models.IntegerField(help_text="position i bogen, højere = senere")
    rating = RatingField(range=5, can_change_vote = True)
    
    class Meta:
        ordering = ['-index']
        get_latest_by = 'pub_date'
    
    def __unicode__(self):
        return self.title
        
    def save(self):
        # to do implement markdown,
        self.mod_date = datetime.now()
        super(Chapter, self).save()
        
    @models.permalink
    def get_absolute_url(self):
        return ('chapter', [str(self.id)])

