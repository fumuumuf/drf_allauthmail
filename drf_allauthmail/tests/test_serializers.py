from allauth.account import utils  as allauth_utils
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.test import TestCase
from drf_allauthmails import app_settings
from drf_allauthmails.serializers import EmailAddressSerializer


class TestCreateArticleSerializer(TestCase):

    def setUp(self):
        self.user = get_user_model()()
        allauth_utils.user_username(self.user, 'spam')
        allauth_utils.user_email(self.user, 'spam@example.com')
        self.user.save()
        allauth_utils.sync_user_email_addresses(self.user)

    def test_serializer_with_empty_data(self):
        serializer = EmailAddressSerializer(user=self.user, data={})
        assert serializer.is_valid() == False

    def test_not_allow_exists_email(self):
        serializer = EmailAddressSerializer(user=self.user, data={'email': 'spam@example.com'})
        assert serializer.is_valid() == False, serializer.errors

    def test_can_save_not_exists_email(self):
        email = 'ham@example.com'
        serializer = EmailAddressSerializer(user=self.user, data={'email': email})
        assert serializer.is_valid() == True, serializer.errors
        obj = serializer.save()
        assert obj.email == email, obj


class TestEmailAddressSerializerVerify(TestCase):

    def setUp(self):
        self.user = get_user_model()()
        self.user.save()
        self.email_txt = 'spam@example.com'
        self.primary_email = EmailAddress.objects.add_email(None, self.user, self.email_txt)
        self.primary_email.set_as_primary()

    def test_verified_email_become_not_primary(self):
        """
            a verified email become not primary if ALLAUTHMAIL_SET_PRIMARY_AT_VERIFIED is not enabled at verified.
        """
        app_settings.ALLAUTHMAIL_SET_PRIMARY_AT_VERIFIED = False

        email = 'ham@example.com'
        serializer = EmailAddressSerializer(user=self.user, data={'email': email})
        serializer.is_valid()
        serializer.save()

        user_email = allauth_utils.user_email(self.user)
        assert user_email == self.email_txt, user_email

        primary_mail = EmailAddress.objects.get_primary(self.user)
        assert primary_mail == self.primary_email, primary_mail

    def test_verified_email_become_primary(self):
        """
            a verified email is made primary if ALLAUTHMAIL_SET_PRIMARY_AT_VERIFIED is enabled at verified.
        """
        app_settings.ALLAUTHMAIL_SET_PRIMARY_AT_VERIFIED = True

        email = 'ham@example.com'
        serializer = EmailAddressSerializer(user=self.user, data={'email': email})
        serializer.is_valid()
        serializer.save()

        user_email = allauth_utils.user_email(self.user)
        assert user_email == email, user_email

        primary_mail = EmailAddress.objects.get_primary(self.user)
        assert primary_mail.email == email, primary_mail

        self.primary_email.refresh_from_db()
        assert self.primary_email.primary == False
