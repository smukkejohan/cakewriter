"""Context Processors for emencia.django.newsletter"""
from emencia.django.newsletter.settings import STATIC_URL


def media(request):
    """Adds media-related context variables to the context"""
    return {'NEWSLETTER_STATIC_URL': STATIC_URL}
