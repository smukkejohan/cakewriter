# -*- coding: utf-8 -*-

from django.contrib import admin
from quiz.models import Category,Quiz,Answer,Question,Score


admin.site.register(Category)
admin.site.register(Quiz)
admin.site.register(Answer)
admin.site.register(Question)
admin.site.register(Score)
