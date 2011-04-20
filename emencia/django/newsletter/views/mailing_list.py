"""Views for emencia.django.newsletter Mailing List"""
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response

from emencia.django.newsletter.utils.tokens import untokenize
from emencia.django.newsletter.models import Newsletter
from emencia.django.newsletter.models import MailingList, Contact
from emencia.django.newsletter.models import ContactMailingStatus

def view_mailinglist_unsubscribe_notrack(request):
    """Unsubscribe a contact to a mailing list"""    
    user_email = request.POST.get('email')
    message=''
    if user_email:
        try:
            contact = Contact.objects.get(email=user_email)
            contactsave = Contact(pk=contact.pk,
                        email=contact.email,
                        first_name=contact.first_name,
                        last_name=contact.last_name,
                        subscriber=False,              
                        content_type=contact.content_type,
                        object_id=contact.object_id,
                        content_object=contact.content_object,
                        creation_date=contact.creation_date,
                        modification_date=contact.modification_date)
            contactsave.save()
            finished = True
            return render_to_response('newsletter/mailing_list_unsubscribe_notrack.html',
                              {'finished':finished},
                              context_instance=RequestContext(request))
        except:
            message="A user with that email does not exist."      
    else:
        message="No email have been entered."  
    return render_to_response('newsletter/mailing_list_unsubscribe_notrack.html',
                              {'message':message},
                              context_instance=RequestContext(request))

def view_mailinglist_unsubscribe(request, slug, uidb36, token):
    """Unsubscribe a contact to a mailing list"""
    newsletter = get_object_or_404(Newsletter, slug=slug)
    contact = untokenize(uidb36, token)

    already_unsubscribed = contact in newsletter.mailing_list.unsubscribers.all()

    if request.POST.get('email') and not already_unsubscribed:
        newsletter.mailing_list.unsubscribers.add(contact)
        newsletter.mailing_list.save()
        already_unsubscribed = True
        ContactMailingStatus.objects.create(newsletter=newsletter, contact=contact,
                                            status=ContactMailingStatus.UNSUBSCRIPTION)

    return render_to_response('newsletter/mailing_list_unsubscribe.html',
                              {'email': contact.email,
                               'already_unsubscribed': already_unsubscribed},
                              context_instance=RequestContext(request))


def view_mailinglist_subscribe(request, form_class, mailing_list_id=None):
    """
    A simple view that shows a form for subscription
    for a mailing list(s).
    """
    subscribed = False
    mailing_list = None
    if mailing_list_id:
        mailing_list = get_object_or_404(MailingList, id=mailing_list_id)

    if request.POST and not subscribed:
        form = form_class(request.POST)
        if form.is_valid():
            form.save(mailing_list)
            subscribed = True
    else:
        form = form_class()

    return render_to_response('newsletter/mailing_list_subscribe.html',
                              {'subscribed': subscribed,
                               'mailing_list': mailing_list,
                               'form': form},
                              context_instance=RequestContext(request))
