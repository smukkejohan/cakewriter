# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User, SiteProfileNotAvailable

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    score = models.IntegerField(default=0)
    level = models.IntegerField(default=0)
    
