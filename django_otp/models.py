from django.db import models


class DeviceManager(models.Manager):
    """
    The :class:`~django.db.models.Manager` object installed as
    ``Device.objects``.
    """
    def from_persistent_id(self, path):
        """
        Loads a device form its persistent id::

            device == Device.objects.from_persistent_id(device.persistent_id)
        """
        from . import import_class

        try:
            device_type, device_id = path.rsplit('/', 1)

            device_cls = import_class(device_type)
            device = device_cls.objects.get(id=device_id)
        except StandardError:
            device = None

        return device

    def devices_for_user(self, user, confirmed=None):
        """
        Returns a queryset for all devices of this class that belong to the
        given user.

        :param user: The user.
        :type user: :class:`~django.contrib.auth.models.User`

        :param confirmed: If ``None``, all matching devices are returned.
            Otherwise, this can be any true or false value to limit the query
            to confirmed or unconfirmed devices, respectively.
        """
        devices = self.model.objects.filter(user=user)
        if confirmed is not None:
            devices = devices.filter(confirmed=bool(confirmed))

        return devices


class Device(models.Model):
    """
    Abstract base model for a :term:`device` attached to a user. Plugins must
    subclass this to define their OTP models.

    .. attribute:: user

        (Model field) Foreign key to :class:`~django.contrib.auth.models.User`.

    .. attribute:: name

        (Model field) A human-readable name to help the user identify their
        devices.

    .. attribute:: confirmed

        (Model field) A boolean value that tells us whether this device has
        been confirmed as valid. It defaults to ``True``, but subclasses or
        individual deployments can force it to ``False`` if they wish to create
        a device and then ask the user for confirmation. As a rule, built-in
        APIs that enumerate devices will only include those that are marked
        confirmed.

    .. attribute:: objects

        A :class:`~django_otp.models.DeviceManager`.
    """
    user = models.ForeignKey('auth.User')
    name = models.CharField(max_length=64)
    confirmed = models.BooleanField(default=True)

    objects = DeviceManager()

    class Meta(object):
        abstract = True

    def __unicode__(self):
        return u'{0}: {1}'.format(self.user.username, self.name)

    @property
    def persistent_id(self):
        return '{0}/{1}'.format(self.import_path, self.id)

    @property
    def import_path(self):
        return '{0}.{1}'.format(self.__module__, self.__class__.__name__)

    def generate_challenge(self):
        """
        Generates a challenge value that the user will need to produce a token.
        This method is permitted to have side effects, such as transmitting
        information to the user through some other channel (email or SMS,
        perhaps). And, of course, some devices may need to commit the
        challenge to the databse.

        :returns: A message to the user. This should be a string that fits
            comfortably in the template ``'OTP Challenge: {0}'``. This may
            return ``None`` if this device is not interactive.
        :rtype: string or ``None``

        :raises: Any StandardError is permitted. Callers should trap
            StandardError and report it to the user.
        """
        return None

    def verify_token(self, token):
        """
        Verifies a token. As a rule, the token will no longer be valid if this
        returns ``True``.

        :param string token: The OTP token provided by the user.
        :rtype: bool
        """
        return False