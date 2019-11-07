from allauth.account import signals
from allauth.account.models import EmailAddress
from allauth.account.utils import sync_user_email_addresses
from django.utils.translation import ugettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .serializers import EmailAddressSerializer


class EmailViewSet(ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet):
    """
    ログインユーザーの email を管理するエンドポイント

    create:
    新しい email を登録します.

    destroy:
    email を削除します. primary の email は削除できません.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = EmailAddressSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        user = self.request.user if self.request else None
        return serializer_class(user=user, *args, **kwargs)

    def initial(self, *args, **kwargs):
        super(EmailViewSet, self).initial(*args, **kwargs)
        # sync the user's email when accessed
        sync_user_email_addresses(self.request.user)

    def get_queryset(self):
        if not self.request or not self.request.user.is_authenticated:  # for api-docs
            return EmailAddress.objects.all()

        return EmailAddress.objects.filter(user=self.request.user)

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


class EmailSubActionAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        queryset = self.request.user.emailaddress_set.filter(id=self.kwargs['pk'])
        obj = get_object_or_404(queryset)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


class SentConfirmationView(EmailSubActionAPIView):
    def post(self, request, *args, **kwargs):
        """
        send confirmation e-mail to a specific e-mail address
        """

        email_address = self.get_object()
        email_address.send_confirmation(self.request)
        return Response({_('Confirmation e-mail sent to the e-mail address')})


class SetAsPrimaryView(EmailSubActionAPIView):
    def put(self, request, *args, **kwargs):
        """
        set a specific e-mail as primary
        """
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
            serializer = EmailAddressSerializer(instance=email_address, user=request.user)
            return Response(serializer.data)


email_list_view = EmailViewSet.as_view(
    {'get': 'list', 'post': 'create'}
)
email_detail_view = EmailViewSet.as_view(
    {'get': 'retrieve', 'delete': 'destroy'}
)

email_set_primary = SetAsPrimaryView.as_view()
email_sent_confirmation = SentConfirmationView.as_view()
