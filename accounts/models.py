# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User, SiteProfileNotAvailable
from datetime import datetime
from django.db.models import signals

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    score = models.IntegerField()
    level = models.IntegerField()
    

## handle scores through a bunch of signals 
# vote post save, comment post save, rate post save
