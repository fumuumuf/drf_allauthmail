from allauth.account import signals
from allauth.account.models import EmailAddress
from allauth.account.utils import sync_user_email_addresses
from django.utils.translation import ugettext as _
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from drf_allauthmails.serializers import EmailAddressSerializer


class EmailViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
    GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = EmailAddressSerializer

    def get_serializer(self, *args, **kwargs):

        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(user=self.request.user, *args, **kwargs)

    def initial(self, *args, **kwargs):
        super(EmailViewSet, self).initial(*args, **kwargs)
        # sync the user's email when accessed
        sync_user_email_addresses(self.request.user)

    def get_queryset(self):
        return self.request.user.emailaddress_set.all()

    def perform_create(self, serializer: Serializer):
        email_address = serializer.save()
        signals.email_added.send(sender=self.request.user.__class__,
                                 request=self.request,
                                 user=self.request.user,
                                 email_address=email_address)

    def perform_destroy(self, instance):
        email_address = instance
        if email_address.primary:
            raise ValidationError(_('You cannot remove your primary e-mail address'))
        else:
            email_address.delete()
            signals.email_removed.send(sender=self.request.user.__class__,
                                       request=self.request,
                                       user=self.request.user,
                                       email_address=email_address)

    @action(methods=['put'], detail=True)
    def set_as_primary(self, request, pk=None):
        email_address = self.get_object()
        if not email_address.verified and \
                EmailAddress.objects.filter(user=request.user,
                                            verified=True).exists():
            raise ValidationError(_('Your primary e-mail address must be verified.'))
        else:
            # Sending the old primary address to the signal
            # adds a db query.
            try:
                from_email_address = EmailAddress.objects \
                    .get(user=request.user, primary=True)
            except EmailAddress.DoesNotExist:
                from_email_address = None
            email_address.set_as_primary()
            signals.email_changed \
                .send(sender=request.user.__class__,
                      request=request,
                      user=request.user,
                      from_email_address=from_email_address,
                      to_email_address=email_address)
            serializer = self.get_serializer(instance=email_address)
            return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def sent_confirmation(self, request, pk=None):
        email_address = self.get_object()
        email_address.send_confirmation(request)
        return Response({_('Confirmation e-mail sent to the e-mail address')})


email_list_view = EmailViewSet.as_view(
    {'get': 'list', 'post': 'create'}
)
email_detail_view = EmailViewSet.as_view(
    {'get': 'retrieve', 'delete': 'destroy'}
)

email_set_primary = EmailViewSet.as_view(
    {'put': 'set_as_primary'}
)

email_sent_confirmation = EmailViewSet.as_view(
    {'post': 'sent_confirmation'}
)
