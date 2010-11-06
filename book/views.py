# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template import RequestContext
from book.models import Chapter

from datetime import datetime

def chapter(request, chapter_id): 
    chapter = Chapter.objects.get(pk=chapter_id)
    return render_to_response(
        'book/chapter.html', {'chapter': chapter,},
        context_instance = RequestContext(request)
    )