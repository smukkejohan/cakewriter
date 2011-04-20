import logging

from django.conf import settings
from django.core.management.base import NoArgsCommand

from html_mailer.engine import organize_all

# allow a sysadmin to pause the sending of mail temporarily.
PAUSE_SEND = getattr(settings, "MAILER_PAUSE_SEND", False)

class Command(NoArgsCommand):
    help = 'Organize email before they are send.'
    
    def handle_noargs(self, **options):
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        logging.info("Organzing emails...")
        # if PAUSE_SEND is turned on don't do anything.
        if not PAUSE_SEND:
            organize_all()
        else:
            logging.info("Organizing is pausing, quitting.")
