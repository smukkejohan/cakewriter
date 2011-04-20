# -*- coding: utf-8 -*-
from settings import CHAPTER_RATING_OPTIONS
from django.shortcuts import render_to_response
from django.template import RequestContext
from book.models import Chapter
from pages.models import Frontpage
from django.http import HttpResponseRedirect
from datetime import datetime

from emencia.django.newsletter.models import Contact
from emencia.django.newsletter.models import MailingList
#Check if email is valid
from django.core.validators import email_re

def is_valid_email(email):
    return True if email_re.match(email) else False


def index(request): 
    chapters = Chapter.objects.filter(visible=True)[:5]
    frontpage = Frontpage.objects.all()
    return render_to_response(
        'index.html', {'chapters': chapters, 'frontpage': frontpage,'options': CHAPTER_RATING_OPTIONS},
        context_instance = RequestContext(request)
    )

def subscribe_resent_chapters(request):
    errors = []
    email = None
    if 'email' in request.POST:
        email = request.POST['email']
    if 'next' in request.POST:
        older_side = request.POST['next']
        if not email:
            errors.append('Please enter your email.')
        elif is_valid_email(email)==False:
            errors.append('The mail is not valid.')
        else:
            contact, created = Contact.objects.get_or_create(email=email,
                                                             defaults={'first_name':email,
                                                                       'last_name': ''})
            if created == False:
                errors.append('The email is already subscribed.')
                return render_to_response(
                    'email_error.html', {'errors': errors, 'email': email, 'older_side': older_side},
                    context_instance = RequestContext(request)
                    )
            #all users is made ready for the ManytoManyField
            subscribers=[]
            contacts = Contact.objects.all()
            for e in contacts:
                subscribers.append(e)
            #Create Maillist with all users
            mailinglists = MailingList.objects.filter(name='All users')
            if mailinglists.count() > 0:
                mailinglist = mailinglists[0]
                mpk = mailinglist.pk
                new_mailing = MailingList(pk=mpk,
                                          name='All users',
                                          description='Mailinglist with all users',
                                          creation_date=mailinglist.creation_date,
                                          modification_date=mailinglist.modification_date,)
            else: 
                new_mailing = MailingList(name='All users',
                                          description='Mailinglist with all users')
            new_mailing.save()
            new_mailing.subscribers.add(*subscribers)
            new_mailing.save()
            
            if request.POST['next']:
                return HttpResponseRedirect(request.POST['next'])
            else:
                return HttpResponseRedirect('/')
    return render_to_response(
        'email_error.html', {'errors': errors, 'email': email, 'older_side': older_side},
        context_instance = RequestContext(request)
        )