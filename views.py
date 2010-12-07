# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template import RequestContext
from book.models import Chapter

from datetime import datetime

def index(request): 
    chapters = Chapter.objects.all()[:5]
    return render_to_response(
        'index.html', {'chapters': chapters,},
        context_instance = RequestContext(request)
    )