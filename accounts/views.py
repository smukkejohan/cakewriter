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
@login_required
def user(request, username):
    users_ori = User.objects.all()
    for user in users_ori:
        try:
            profile = user.get_profile()
        except ObjectDoesNotExist:
            profile = Profile(user=user)
            profile.save()
    users = Profile.objects.all().order_by('-score')
    user = None
    editable = False
    usercomments = None
    userchapters = None
    userrevisions = None
    userratings = None
    activity = False
    try:
        user = User.objects.get(username=username)
    except:
        pass
    if user==request.user:
        editable = True
    if user:
        #create profile if none
        try:
            profile = user.get_profile()
        except ObjectDoesNotExist:
            profile = Profile(user=user)
            profile.save()
        #Comments
        usercomments = Comment.objects.filter(user=user).order_by('content_type')
        userchapters = Chapter.objects.filter(author=user, visible=True)
        userrevisions = Revision.objects.filter(revision_user=user).exclude(counter=1)
        userratings = Vote.objects.filter(user=user)
        if (usercomments or userchapters or userrevisions or userratings): activity=True
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

@login_required
def edit_profile(request):
    try:
        profile = request.user.get_profile()
    except ObjectDoesNotExist:
        profile = Profile(user=request.user)
        profile.save()
    user = request.user
    users_ori = User.objects.all()
    for user_ori in users_ori:
        try:
            profile = user_ori.get_profile()
        except ObjectDoesNotExist:
            profile = Profile(user=user_ori)
            profile.save()
    users = Profile.objects.all().order_by('-score')
    if request.method == 'POST':
        form = ProfileUserForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/users/username/'+request.user.username+'/')
        else:
          form = ProfileUserForm(request.POST, request.FILES, instance=profile)  
    else:
        form = ProfileUserForm(instance=profile)
    return render_to_response('accounts/user_edit.html', {'form': form,'users':users,'user':user},context_instance = RequestContext(request))
