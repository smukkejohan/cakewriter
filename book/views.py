# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template import RequestContext
from book.models import Chapter
from djangoratings.views import AddRatingFromModel
from django.http import HttpResponse
from django.core import serializers

def chapter(request, chapter_id): 
    chapter = Chapter.objects.get(pk=chapter_id)
    return render_to_response(
        'book/chapter.html', {'chapter': chapter,},
        context_instance = RequestContext(request)
    )
    
    
    
    
def rate_chapter(request, chapter_id):
    
    # if get then, login/registration then rate
    
    if request.POST:
        rate = request.POST.get('rate')
            
        params = {
            'app_label': 'book',
            'model': 'chapter',
            'object_id': chapter_id,
            'field_name': 'rating', # this should match the field name defined in your model
            'score': rate, # the score value they're sending
        }
        response = AddRatingFromModel()(request, **params)
        
        chapter = Chapter.objects.get(pk=chapter_id)
        ##score = chapter.rating.get_rating(request.user, request.META['REMOTE_ADDR'])
    

        #json_serializer = serializers.get_serializer("json")()
        #json_response = json_serializer.serialize(response_dict, ensure_ascii=False, stream=response)
        return HttpResponse(response, mimetype="application/javascript")
        


