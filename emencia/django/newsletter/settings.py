"""Settings for emencia.django.newsletter"""
from django.conf import settings

USE_WORKGROUPS = getattr(settings, 'NEWSLETTER_USE_WORKGROUPS', False)

INCLUDE_UNSUBSCRIPTION = getattr(settings, 'NEWSLETTER_INCLUDE_UNSUBSCRIPTION', True)

DEFAULT_HEADER_REPLY = getattr(settings, 'NEWSLETTER_DEFAULT_HEADER_REPLY', 'noreply@winning-without-losing.com')
DEFAULT_HEADER_SENDER = getattr(settings, 'NEWSLETTER_DEFAULT_HEADER_SENDER', 'noreply@winning-without-losing.com')

TRACKING_LINKS = getattr(settings, 'NEWSLETTER_TRACKING_LINKS', True)
TRACKING_IMAGE = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAAAXNSR0IArs4c6QAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9kKEwwvINGR5lYAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC'

STATIC_URL = getattr(settings, 'NEWSLETTER_STATIC_URL', '/edn/')

NEWSLETTER_BASE_PATH = getattr(settings, 'NEWSLETTER_BASE_PATH', 'uploads/newsletter')
