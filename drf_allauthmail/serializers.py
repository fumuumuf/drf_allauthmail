from allauth.account.forms import AddEmailForm
from allauth.account.models import EmailAddress
from rest_framework import serializers


class EmailAddressSerializer(serializers.ModelSerializer):
    form_class = AddEmailForm

    class Meta:
        model = EmailAddress
        exclude = ('user',)
        extra_kwargs = {
            'verified': {'read_only': True}
            , 'primary': {'read_only': True}
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(EmailAddressSerializer, self).__init__(*args, **kwargs)

    def validate_email(self, val):
        if self.instance is not None:
            return val

        # Create AddEmailForm with the serializer
        self.email_form = self.form_class(data={'email': val, 'user': self.user})

        if not self.email_form.is_valid():
            raise serializers.ValidationError(self.email_form.errors)
        return val

    def create(self, validated_data):
        """
        create a entity with send confirm e-mail
        """
        return EmailAddress.objects.add_email(self.get_request(),
                                              self.user,
                                              validated_data['email'],
                                              confirm=True)

    def get_request(self):
        return self.context.get('request')
