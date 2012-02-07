# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import render_to_response
from django.template import RequestContext
from book.models import Chapter, UserChapter
from djangoratings.views import AddRatingFromModel
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson as json
from django.contrib.sites.models import Site
from django.contrib.comments.models import Comment
from book.utils import sanitizeHtml
from settings import CHAPTER_RATING_OPTIONS
from django.shortcuts import redirect, get_object_or_404
from django.core import serializers
from django.contrib.contenttypes.models import ContentType
from simplewiki.models import Article
from djangoratings.models import Vote
from usermessage.models import UserMessage
from tagging.views import tagged_object_list
from tagging.models import TaggedItem
import random

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
    

def all_chapters(request): 
    best_chapters = Chapter.objects.filter(visible=True).extra(select={'r': '((100/%s*rating_score/(rating_votes+%s))+100)/2' % (Chapter.rating.range, Chapter.rating.weight)}).order_by('-r')[:5]
    new_chapters = Chapter.objects.filter(visible=True)[:5]
    return render_to_response(
        'book/all_chapters.html', {'new_chapters':new_chapters,'best_chapters':best_chapters,'options': CHAPTER_RATING_OPTIONS},
        context_instance = RequestContext(request)
    )

def tagged_chapters(request,tag):
    chapters = Chapter.objects.filter(visible=True).extra(select={'r': '((100/%s*rating_score/(rating_votes+%s))+100)/2' % (Chapter.rating.range, Chapter.rating.weight)}).order_by('-r')
    return tagged_object_list(request, chapters, tag, paginate_by=10,
                              allow_empty=True, template_object_name='chapters',extra_context={'options':CHAPTER_RATING_OPTIONS})
    
def chapter(request, chapter_id):
    chapters = Chapter.objects.filter(visible=True).extra(select={'r': '((100/%s*rating_score/(rating_votes+%s))+100)/2' % (Chapter.rating.range, Chapter.rating.weight)}).order_by('-r')
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    chapter_type = ContentType.objects.get_for_model(chapter)
    try:
        vote = Vote.objects.get(object_id=chapter.pk, content_type=chapter_type, user=request.user).score
    except:
        vote = 0
    
    try:
        related_wiki = Article.objects.get(chapter_related=chapter)
    except MultipleObjectsReturned:
        related_wiki = Article.objects.filter(chapter_related=chapter)[0]       
    except ObjectDoesNotExist:
        related_wiki = None
    
    try:
        related_chapters = TaggedItem.objects.get_related(chapter, Chapter)
        related_chapters = random.sample(related_chapters,5)
    except:
        related_chapters = []
    
    if chapter.rating.score == 0 or chapter.rating.votes == 0:
        score = chapter.rating.score
    else:
        score = chapter.rating.score / chapter.rating.votes
    
    #check if any user message should be deleted
    if request.GET and not request.user.is_anonymous():
        if 'usermessage' in request.GET:
            usermessage_id = int(request.GET['usermessage'])
            try:
                usermessage = UserMessage.objects.get(pk=usermessage_id, user=request.user)
                usermessage.delete()
            except:
                error = "Notification could not be deleted"
    
    #return
    return render_to_response(
        'book/chapter.html', {'related_wiki': related_wiki, 'chapter': chapter, 'chapters': chapters, 'options': CHAPTER_RATING_OPTIONS, 'score': str(score), 'rating_on_chapter':vote, 'related_chapters':related_chapters},
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
from book.forms import UserChapterForm
from html2text import html2text
from django.db.models import Max
from datetime import datetime
def user_chapter(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            form = UserChapterForm(request.POST, request.FILES)
            if form.is_valid():
                title = form.cleaned_data['title']
                summary_html = form.cleaned_data['summary']
                content = form.cleaned_data['content']
                photo = form.cleaned_data['photo']
                tags_string = form.cleaned_data['tags_string']
                
                highest_index = Chapter.objects.aggregate(Max('index'))
                index = highest_index['index__max']+1
                
                user_chapter = UserChapter(title=title,
                                       summary=summary_html,
                                       summary_html=sanitizeHtml(summary_html),
                                       body=content,
                                       body_html=sanitizeHtml(content),
                                       pub_date=datetime.now(),
                                       index=index,
                                       author=request.user,
                                       picture=photo,
                                       tags_string=tags_string)
                user_chapter.save()
                return HttpResponseRedirect('/book/user_chapter/thanks/')
            else:
                data = {'title':request.POST['title'],
                        'summary':request.POST['summary'],
                        'content':request.POST['content'],
                        'photo':request.FILES['photo'],
                        'tags_string':request.FILES['tags_string']}
                form = UserChapterForm(data)
                return render_to_response('book/user_chapter.html', 
                                        {'form': form,},
                                        context_instance = RequestContext(request))
        else:
            form = UserChapterForm()
    
        return render_to_response('book/user_chapter.html', 
                                {'form': form,},
                                context_instance = RequestContext(request))
    else:
       return HttpResponseRedirect('/accounts/login/?next=/book/user_chapter/') 
def user_chapter_thanks(request):
    chapters = Chapter.objects.filter(visible=True).order_by('-pub_date')
    return render_to_response('book/user_chapter_thanks.html',
                                {'chapters': chapters,},
                                context_instance = RequestContext(request))