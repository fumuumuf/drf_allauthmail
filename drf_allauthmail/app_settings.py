from django.conf import settings

ALLAUTHMAIL_SET_PRIMARY_AT_VERIFIED = getattr(settings, 'ALLAUTHMAIL_SET_PRIMARY_AT_VERIFIED', False)
