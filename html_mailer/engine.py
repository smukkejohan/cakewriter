# coding: utf-8
import time
import smtplib
import logging
from lockfile import FileLock, AlreadyLocked, LockTimeout
from socket import error as socket_error

from html_mailer.models import Message, DontSendEntry, MessageLog

from django.conf import settings
from django.core.mail import send_mail as core_send_mail

# when queue is empty, how long to wait (in seconds) before checking again
EMPTY_QUEUE_SLEEP = getattr(settings, "MAILER_EMPTY_QUEUE_SLEEP", 30)

# lock timeout value. how long to wait for the lock to become available.
# default behavior is to never wait for the lock to be available.
LOCK_WAIT_TIMEOUT = getattr(settings, "MAILER_LOCK_WAIT_TIMEOUT", -1)


def prioritize():
    """
    Yield the messages in the queue in the order they should be sent.
    """
    
    while True:
        while Message.objects.high_priority().count() or Message.objects.medium_priority().count():
            while Message.objects.high_priority().count():
                for message in Message.objects.high_priority().order_by('when_added'):
                    yield message
            while Message.objects.high_priority().count() == 0 and Message.objects.medium_priority().count():
                yield Message.objects.medium_priority().order_by('when_added')[0]
        while Message.objects.high_priority().count() == 0 and Message.objects.medium_priority().count() == 0 and Message.objects.low_priority().count():
            yield Message.objects.low_priority().order_by('when_added')[0]
        if Message.objects.non_deferred().count() == 0:
            break


def organize_all():
    from emencia.django.newsletter.models import Contact
    from django.contrib.auth.models import User 
    from usermessage.models import UserMessage, StandardUserMessage
    from djangoratings.models import Vote, Score
    from book.models import Chapter
    from django.template import Context
    from django.template.loader import get_template
    from accounts.models import ScoreLog, Profile
    from simplewiki.models import Revision
    from django.contrib.comments.models import Comment
    from django.core.exceptions import ObjectDoesNotExist
    from BeautifulSoup import BeautifulSoup
    
    contacts = Contact.objects.all()
    staff_usermessages = weeklymessages = StandardUserMessage.objects.all()
    
    for contact in contacts:
        if contact.subscriber==True:
            comments_on_comments = UserMessage.objects.filter(contact=contact, category=1)
            comments_on_revisions = UserMessage.objects.filter(contact=contact, category=3)
            new_chapters = UserMessage.objects.filter(contact=contact, category=4)
            #revisions_on_revisions = UserMessage.objects.filter(contact=contact, category=2)

            #Only for users
            if contact.content_object:
                user = contact.content_object
                
                try:
                    profile = user.get_profile()
                except ObjectDoesNotExist:
                    p = Profile(user=user)
                    p.save()
                
                submitted_chapters  = Chapter.objects.filter(author=user)
                edited_chapters     = Revision.objects.filter(revision_user=user).exclude(counter=1)
                commented_chapters  = Comment.objects.filter(user=user).order_by('content_type')
                
                rated_chapters                       = Vote.objects.filter(user=user)
                given_positive_votes_on_comments     = ScoreLog.objects.filter(profile=profile,points=1,ctype='vote')
                received_positive_votes_on_comments  = ScoreLog.objects.filter(profile=profile,points=2,ctype='commentvoted')
                received_negative_votes_on_comments  = ScoreLog.objects.filter(profile=profile,points=-1,ctype='commentvoted')
            else:
                user = None
                
                submitted_chapters   = None
                edited_chapters      = None
                commented_chapters   = None
                
                rated_chapters                        = None
                given_positive_votes_on_comments      = None
                received_positive_votes_on_comments   = None
                received_negative_votes_on_comments   = None
                
            #create message if any
            if comments_on_comments or comments_on_revisions or new_chapters or staff_usermessages or user:
                plaintext = get_template('email/weekly_newsletter.txt')
                html = get_template('email/weekly_newsletter.html')               
                                
                c = Context({   'contact'                               : contact, 
                                'comments_on_comments'                  : comments_on_comments,
                                'comments_on_revisions'                 : comments_on_revisions,
                                'new_chapters'                          : new_chapters,
                                'staff_usermessages'                    : staff_usermessages,
                                'user'                                  : user,
                                'submitted_chapters'                    : submitted_chapters,
                                'edited_chapters'                       : edited_chapters,
                                'commented_chapters'                    : commented_chapters,
                                'rated_chapters'                        : rated_chapters,
                                'given_positive_votes_on_comments'      : given_positive_votes_on_comments,
                                'received_positive_votes_on_comments'   : received_positive_votes_on_comments,
                                'received_negative_votes_on_comments'   : received_negative_votes_on_comments,
                            })
                email_plaintext = plaintext.render(c)
                email_html = html.render(c)

                soup = BeautifulSoup(email_html)
                for link_markup in soup('a'):
                    link_markup['style'] = 'color:#16AAD7;'
                for header_markup in soup('h3'):
                    header_markup['style'] = 'border-bottom:8px solid #ecebe8;margin-bottom:0px;padding-bottom:5px;'
                email_html = soup.prettify()

                final_mail = Message(to_address=contact.email,
                                    from_address='noreply@winning-without-losing.com',
                                    subject='Updates from winning-without-losing',
                                    message_text=email_plaintext,
                                    message_html=email_html
                                    )
                final_mail.save()
                logging.info("Organizing message to %s" % final_mail.to_address.encode("utf-8"))
                
                comments_on_comments.delete()
                comments_on_revisions.delete()
                new_chapters.delete()

    staff_usermessages.delete()
    
def send_all():            
    """
    Send all eligible messages in the queue.
    """
    
    lock = FileLock("send_mail")
    
    logging.debug("acquiring lock...")
    try:
        lock.acquire(LOCK_WAIT_TIMEOUT)
    except AlreadyLocked:
        logging.debug("lock already in place. quitting.")
        return
    except LockTimeout:
        logging.debug("waiting for the lock timed out. quitting.")
        return
    logging.debug("acquired.")
    
    start_time = time.time()
    
    dont_send = 0
    deferred = 0
    sent = 0
    
    try:
        for message in prioritize():
            if DontSendEntry.objects.has_address(message.to_address):
                logging.info("skipping email to %s as on don't send list " % message.to_address)
                MessageLog.objects.log(message, 2) # @@@ avoid using literal result code
                message.delete()
                dont_send += 1
            else:
                try:
                    logging.info("sending message '%s' to %s" % (message.subject.encode("utf-8"), message.to_address.encode("utf-8")))
                    
                    if message.message_html is None:
                        """ Send as plain text if no html has been provided. """
                        core_send_mail(message.subject, message.message_text, message.from_address, [message.to_address])
                    else:                    
                        """ Otherwise, send as HTML. """
                        from django.core.mail import EmailMultiAlternatives
                        msg = EmailMultiAlternatives(message.subject, message.message_text, message.from_address, [message.to_address])
                        msg.attach_alternative(message.message_html, "text/html")
                        msg.send()
                    
                    MessageLog.objects.log(message, 1) # @@@ avoid using literal result code
                    message.delete()
                    sent += 1
                except (socket_error, smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused, smtplib.SMTPAuthenticationError), err:
                    message.defer()
                    logging.info("message deferred due to failure: %s" % err)
                    MessageLog.objects.log(message, 3, log_message=str(err)) # @@@ avoid using literal result code
                    deferred += 1
    finally:
        logging.debug("releasing lock...")
        lock.release()
        logging.debug("released.")
    
    logging.info("")
    logging.info("%s sent; %s deferred; %s don't send" % (sent, deferred, dont_send))
    logging.info("done in %.2f seconds" % (time.time() - start_time))

def send_loop():
    """
    Loop indefinitely, checking queue at intervals of EMPTY_QUEUE_SLEEP and
    sending messages if any are on queue.
    """
    
    while True:
        while not Message.objects.all():
            logging.debug("sleeping for %s seconds before checking queue again" % EMPTY_QUEUE_SLEEP)
            time.sleep(EMPTY_QUEUE_SLEEP)
        send_all()
