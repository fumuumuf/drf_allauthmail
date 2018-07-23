from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase


class EmailListTest(APITestCase):
    def _create_users(self):
        self.user1 = get_user_model().objects.create(username='user1', email="user1@example.com")
        self.user2 = get_user_model().objects.create(username='user2', email="user2@example.com")
        for i in range(5):
            EmailAddress.objects.create(user=self.user2, email='user2{}@example.com'.format(i))

    def setUp(self):
        self.url = '/email/'
        self._create_users()

    def test_anonymous_user_cant_access(self):
        response = self.client.get(self.url)
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN), response.status_code

    def test_list(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK, response.status_code
        response_json = response.json()
        assert len(response_json['results']) == 1, response_json

        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK, response.status_code
        response_json = response.json()
        assert len(response_json['results']) == 6, response_json

    def test_add_email_with_send_confirm_mail(self):
        self.client.force_authenticate(user=self.user1)
        email = 'user1_2@example.com'
        response = self.client.post(self.url, {'email': email})
        assert response.status_code == status.HTTP_201_CREATED, response.status_code
        response_json = response.json()
        assert response_json['email'] == email, response_json

        # test send email
        assert len(mail.outbox), 1
        assert email in mail.outbox[0].to, mail.outbox[0].to
        assert mail.outbox[0].subject.endswith('Please Confirm Your E-mail Address'), mail.outbox[0].subject


def detail_url(pk):
    return '/email/{}/'.format(pk)


def confirmation_url(pk):
    return '/email/{}/sent_confirmation/'.format(pk)


def primary_url(pk):
    return '/email/{}/set_primary/'.format(pk)


class EmailDetailTest(APITestCase):
    def _create_users(self):
        self.user1 = get_user_model().objects.create(username='user1')
        email_address = EmailAddress.objects.create(user=self.user1, email='user1primary@example.com')
        email_address.set_as_primary()
        for i in range(3):
            EmailAddress.objects.create(user=self.user1, email='user1{}@example.com'.format(i))

        self.user2 = get_user_model().objects.create(username='user2')
        EmailAddress.objects.create(user=self.user2, email='user2@example.com')

    def setUp(self):
        self._create_users()

    def test_can_access_email_owned_by_logged_in_user(self):
        self.client.force_authenticate(user=self.user1)
        email = self.user1.emailaddress_set.first()

        url = detail_url(email.id)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json['email'] == email.email, response_json

    def test_cannot_access_email_owned_by_other(self):
        self.client.force_authenticate(user=self.user2)
        email = self.user1.emailaddress_set.first()

        url = detail_url(email.id)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND, url

    def test_cannot_remove_primary_email(self):
        self.client.force_authenticate(user=self.user1)
        email = EmailAddress.objects.get_primary(self.user1)
        url = detail_url(email.id)
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.status_code

    #
    def test_remove_non_primary_email(self):
        self.client.force_authenticate(user=self.user1)
        email = self.user1.emailaddress_set.filter(primary=False).first()
        url = detail_url(email.id)
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT, response.status_code

    def test_sent_confirm(self):
        self.client.force_authenticate(user=self.user1)
        email = self.user1.emailaddress_set.first()

        url = confirmation_url(email.id)
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK, response.status_code

        # test send email
        assert len(mail.outbox), 1
        assert email.email in mail.outbox[0].to, mail.outbox[0].to
        assert mail.outbox[0].subject.endswith('Please Confirm Your E-mail Address'), mail.outbox[0].subject

    def test_non_verified_email_cannot_be_primary_when_verified_emails_exist(self):
        self.client.force_authenticate(user=self.user1)
        emails = self.user1.emailaddress_set.filter(primary=False).all()
        verified_email = emails[0]
        verified_email.verified = True
        verified_email.save()

        email = emails[1]
        url = primary_url(email.id)
        response = self.client.put(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.status_code

    def test_non_verified_email_can_be_primary_when_all_email_not_verified(self):
        self.client.force_authenticate(user=self.user1)
        pre_primary_mail_id = EmailAddress.objects.get_primary(self.user1).id
        email = self.user1.emailaddress_set.filter(primary=False).first()

        url = primary_url(email.id)
        response = self.client.put(url)
        assert response.status_code == status.HTTP_200_OK, response.status_code

        assert EmailAddress.objects.get(id=pre_primary_mail_id).primary == False
        assert EmailAddress.objects.get(id=email.id).primary == True

    def test_verified_email_can_be_primary(self):
        self.client.force_authenticate(user=self.user1)
        emails = self.user1.emailaddress_set.filter(primary=False).all()
        verified_email = emails[0]
        verified_email.verified = True
        verified_email.save()

        url = primary_url(verified_email.id)
        response = self.client.put(url)
        assert response.status_code == status.HTTP_200_OK, response.status_code
        assert EmailAddress.objects.get(id=verified_email.id).primary == True
