from django.db import models
from django.db.models import Q
from dmutex.models import MutexEvent

### Base event
class Event(MutexEvent):
    description = models.CharField(max_length=100)

### For advanced usage
class Room(models.Model):
    name = models.CharField(max_length=255)
    can_parallel = models.BooleanField(default=False)

class Booking(MutexEvent):
    room = models.ForeignKey(Room)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class MutexMeta:
        collision_fields = ['room']
        exclude = Q(room__can_parallel=True) | Q(deleted_at__isnull=False)


class RequestedBooking(MutexEvent):
    request = models.CharField(max_length=100, default='room')
    room = models.ForeignKey(Room, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class MutexMeta:
        collision_fields = ['room']
        exclude = Q(room__can_parallel=True) | Q(deleted_at__isnull=False)