from django.db import models
from mutex.models import MutexEvent

class Event(MutexEvent):
    description = models.CharField(max_length=100)