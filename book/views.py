# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template import RequestContext
from book.models import Chapter
from djangoratings.views import AddRatingFromModel
from django.http import HttpResponse
from django.utils import simplejson as json
from django.contrib.sites.models import Site
from django.contrib.comments.models import Comment
from settings import CHAPTER_RATING_OPTIONS
from django.shortcuts import redirect, get_object_or_404
from django.core import serializers
from django.contrib.contenttypes.models import ContentType


def api_get_chapters(request):
    chapters = Chapter.objects.all()
    
    json_serializer = serializers.get_serializer("json")()
    json_response = json_serializer.serialize(chapters, ensure_ascii=False)

    return HttpResponse(json_response, mimetype="application/javascript")


def api_get_chapter(request, chapter_id):
    chapter = Chapter.objects.get(pk=chapter_id)
    
    json_serializer = serializers.get_serializer("json")()
    json_response = json_serializer.serialize([chapter,], ensure_ascii=False)
    
    return HttpResponse(json_response, mimetype="application/javascript")

def api_get_comments_for_chapter(request, chapter_id):
    chapter = Chapter.objects.get(pk=chapter_id)
    
    content_type = ContentType.objects.get_for_model(Chapter)
    
    comments = Comment.objects.filter(object_pk=chapter.id, content_type=content_type)
    
    json_serializer = serializers.get_serializer("json")()
    json_response = json_serializer.serialize(comments, ensure_ascii=False)
    
    return HttpResponse(json_response, mimetype="application/javascript")
    
  
    
def chapter(request, chapter_id): 
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    
    score = chapter.rating.score / chapter.rating.votes
    
    return render_to_response(
        'book/chapter.html', {'chapter': chapter, 'options': CHAPTER_RATING_OPTIONS, 'score': str(score)},
        context_instance = RequestContext(request)
    )

def rating_widget(request, chapter_id):
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    
    domain = Site.objects.get_current().domain
    
    return render_to_response(
        'book/rating_widget.html', {'chapter': chapter, 'options': CHAPTER_RATING_OPTIONS, 'domain': domain},
        context_instance = RequestContext(request)
    )



    

      
def rate_chapter(request, chapter_id, score = None):
    """
    
    """
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    
    if request.method == 'GET':
        if score:
            if request.user.is_authenticated():
                return render_to_response(
                    'book/rate_confirmation.html', {'chapter': chapter, 'score': score},
                    context_instance = RequestContext(request)
                ) 
            
            else:
                request.session['pendingrating_chapter'] = chapter_id
                request.session['pendingrating_score'] = score
                
                return render_to_response(
                    'book/rate_chapter.html', {'chapter': chapter,},
                    context_instance = RequestContext(request)
                )        
        else:
            return redirect(chapter)  
            
    else:
        score = request.POST.get('score')
            
        params = {
            'app_label': 'book',
            'model': 'chapter',
            'object_id': chapter_id,
            'field_name': 'rating',
            'score': score,
        }
        response = AddRatingFromModel()(request, **params)
        
        chapter = Chapter.objects.get(pk=chapter_id)
        
        if request.is_ajax():      
            return HttpResponse(response, mimetype="application/javascript")
        else:
            return redirect(chapter)
        

##score = chapter.rating.get_rating(request.user, request.META['REMOTE_ADDR'])  


