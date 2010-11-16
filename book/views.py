# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template import RequestContext
from book.models import Chapter
from djangoratings.views import AddRatingFromModel
from django.http import HttpResponse
from django.utils import simplejson


from django.shortcuts import redirect, get_object_or_404


def chapter(request, chapter_id): 
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    return render_to_response(
        'book/chapter.html', {'chapter': chapter,},
        context_instance = RequestContext(request)
    )

def rating_widget(request, chapter_id):
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    
    OPTIONS = (
        ('1', 'Very poor'),
        ('2', 'Not that bad'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Perfect'),
    )
    
    return render_to_response(
        'book/rating_widget.html', {'chapter': chapter, 'options': OPTIONS},
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
#json_serializer = serializers.get_serializer("json")()
#json_response = json_serializer.serialize(response_dict, ensure_ascii=False, stream=response)

