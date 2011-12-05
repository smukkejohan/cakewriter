from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from accounts.forms import ProfileForm, ProfileUserForm
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from accounts.models import Profile
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.comments.models import Comment
from book.models import Chapter
from simplewiki.models import Revision
from djangoratings.models import Vote

def users(request):
    users = Profile.objects.all().order_by('-score')
    users_with_picture = Profile.objects.exclude(photo="").order_by('?')
    
    return render_to_response('accounts/users.html', 
                                {'users': users,
                                'users_with_picture': users_with_picture,
                                },
                                context_instance = RequestContext(request)
                             )

def user(request, username):
    users = Profile.objects.all().order_by('-score')
    #The user that is being viewed
    try:
        user = User.objects.get(username=username)
    except:
        user = None
    #if the user being viewed is the same as the on logged on then give him permission to edit
    if user==request.user:
        editable = True
    else:
        editable = False   
    if user:
        #create profile if none
        try:
            profile = user.get_profile()
        except ObjectDoesNotExist:
            profile = Profile(user=user)
            profile.save()
        usercomments = Comment.objects.filter(user=user).order_by('content_type')
        userchapters = Chapter.objects.filter(author=user, visible=True)
        userrevisions = Revision.objects.filter(revision_user=user).exclude(counter=1)
        userratings = Vote.objects.filter(user=user)
        if (usercomments or userchapters or userrevisions or userratings): activity=True
        else: activity = False
        return render_to_response('accounts/user.html', 
                                    {'editable': editable,
                                    'profile': user,
                                    'users':users, 
                                    'username':username,
                                    'usercomments':usercomments,
                                    'userchapters':userchapters,
                                    'userrevisions':userrevisions,
                                    'userratings':userratings,
                                    'activity':activity,
                                    },
                                    context_instance = RequestContext(request)
                                 )
    else:
        activity = False
        return render_to_response('accounts/user.html', 
                        {'editable': editable,
                        'profile': user,
                        'users':users, 
                        'username':username,
                        'activity':activity,
                        },
                        context_instance = RequestContext(request)
                     )

@login_required
def edit_profile(request):
    try:
        profile = request.user.get_profile()
    except ObjectDoesNotExist:
        profile = Profile(user=request.user)
        profile.save()
    user = request.user
    users = Profile.objects.all().order_by('-score')
    if request.method == 'POST':
        form = ProfileUserForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/users/'+request.user.username+'/')
        else:
          form = ProfileUserForm(request.POST, request.FILES, instance=profile)  
    else:
        form = ProfileUserForm(instance=profile)
    return render_to_response('accounts/user_edit.html', {'form': form,'users':users,'user':user},context_instance = RequestContext(request))

@login_required
def account(request):
    return HttpResponseRedirect('/users/'+request.user.username+'/')