from allauth.account import utils  as allauth_utils
from django.contrib.auth import get_user_model
from django.test import TestCase

from drf_allauthmail.serializers import EmailAddressSerializer


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
