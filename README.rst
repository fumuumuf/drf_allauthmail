===============
drf_allauthmail
===============

drf_allauthmail provide REST endpoints of allauth's EmailAddress Model.

Quick start
-----------

1. Add "polls" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'drf_allauthmail',
    ]

2. Include the polls URLconf in your project urls.py like this::

    path('mails/', include('drf_allauthmail.urls')),

3. Visit http://127.0.0.1:8000/mails/ to refer your e-mail addresses.
