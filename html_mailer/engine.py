# coding: utf-8
import time
import smtplib
import logging
from lockfile import FileLock, AlreadyLocked, LockTimeout
from socket import error as socket_error

from html_mailer.models import Message, DontSendEntry, MessageLog, Organizer

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
    #Check if user have been active within a week
    from emencia.django.newsletter.models import Contact
    from django.contrib.auth.models import User 
    from datetime import datetime, timedelta
    from markdown import markdown
    from django.contrib.sites.models import Site
    now = datetime.now()
    contacts = Contact.objects.all()
    for contact in contacts:
        if contact.subscriber==True:    
            message = ''
            c_c = Organizer.objects.filter(user=contact, category=1)
            r_r = Organizer.objects.filter(user=contact, category=2)
            c_r = Organizer.objects.filter(user=contact, category=3)
            nc = Organizer.objects.filter(user=contact, category=4)
            #count how many of each
            inactive_count = 0
            c_r_count = 0
            r_r_count = 0
            c_c_count = 0
            new_chapter_count = 0
            #Only for users
            if contact.content_object:
                if now - contact.content_object.last_login>timedelta(7) and now - contact.content_object.last_login<timedelta(8):
                    message+="We haven't seen you for a while on Winning-Without-Losing. New chapters have been added, go check them out here: [Click here](%s)\n\n" % Site.objects.get_current()
                    inactive_count+=1
                if c_r:
                    message+= '###New comment on one of your chapter revisions\n'
                for mails in c_r:
                    message+='%s\n\n' % mails.message
                    mails.delete()
                    c_r_count+=1
                if r_r:
                    message+= '###New chapter revision of the same chapter you have edited\n'
                for mails in r_r:
                    message+='%s\n\n' % mails.message
                    mails.delete()
                    r_r_count+=1
                if c_c:
                    message+= '###New comment where you have commented\n'
                for mails in c_c:
                    message+='%s\n\n' % mails.message
                    mails.delete()
                    c_c_count+=1
            #New chapters for all subscribers
            if nc:
                message+= '###New chapters have been submitted!\n'
            for mails in nc:
                message+='%s\n\n' % mails.message
                mails.delete()
                new_chapter_count+=1
            #finish
            if message !='':
                message="Hi %s, here is an update on what happened on Winning Without Losing this week.\n\n&nbsp;\n\n%s" % (contact.first_name, message)
                message+="&nbsp;\n\nThat's all for today... But the quest for a better entrepreneurial life keeps on!\n\n&nbsp;\n\nWinning Without Losing\n\nwww.winning-without-losing.com\n\n<img src=\"http://m.winning-without-losing.com/img/logo.jpg\" />\n\n\nif you want to unsubscribe from this weekly update [click here](http://%s/newsletters/mailing/unsubscribe/)" % Site.objects.get_current()
                #create html message with style
                html_start = '<div style="width:100%; height:100%; margin:0px; background-color:#d3d8dd;"><div style="background-color:#d3d8dd;"><div style="padding:50px 0px 50px 0px;"><div style="margin:0px auto 0px auto; background-color:#FFF; width:600px; padding-bottom:30px;font-family: Helvetica, Verdana, Arial, sans-serif;-moz-box-shadow:  0px 0px 50px 0px #3d3d3d; -webkit-box-shadow: 0px 0px 50px 0px #3d3d3d; box-shadow: 0px 0px 50px 0px #3d3d3d;"><div style="height:50px;background-color:#01a3d4; padding:40px 0px 40px 30px; font-size:20px; font-weight: bold; font-size: 50px; color:#FFF; text-shadow: #000 0px -1px 0px;">Updates from WWL</div><div style="margin:50px 50px 0px 50px; color:#565454;">'
                html_end = '</div></div></div></div></div>'
                message_html = html_start+markdown(message)+html_end
                #create message
                final_mail = Message(to_address=contact.email,
                     from_address='noreply@winning-without-losing.com',
                     subject='Updates from winning-without-losing',
                     message_text=message,
                     message_html=message_html)
                final_mail.save()
                logging.info("Organizing message to %s with: %s inactive, %s c-r, %s r-r, %s c-c, %s new chapters" % (final_mail.to_address.encode("utf-8"),inactive_count,c_r_count,r_r_count,c_c_count,new_chapter_count))

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
