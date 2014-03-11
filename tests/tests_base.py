import datetime
from .models import Event
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from mutex.models import MutexEvent, MutexQuerySet
from mutex.debug import CollisionException
from django.core.exceptions import ValidationError


class BaseEventTest(TestCase):
    def setUp(self):
        self.event = Event(start_time=datetime.datetime.now(), description="Event 1")
        self.event.end_time = self.event.start_time + relativedelta(minutes=60)
        self.event.save()

    def test_queryset_retval(self):
        assert isinstance(Event.objects.all(), MutexQuerySet)

    def test_detect_overlapping(self):
        ### Start and end at the same time
        start = self.event.start_time
        end = self.event.end_time
        count = Event.objects.overlapping_events(start=start, end=end).count()
        self.assertEqual(count, 1)
        ### Start earlier and ends later
        start = self.event.start_time - relativedelta(minutes=5)
        end = self.event.end_time + relativedelta(minutes=5)
        count = Event.objects.overlapping_events(start=start, end=end).count()
        self.assertEqual(count, 1)
        ### Start earlier, end earlier
        start = self.event.start_time - relativedelta(minutes=5)
        end = self.event.end_time - relativedelta(minutes=5)
        count = Event.objects.overlapping_events(start=start, end=end).count()
        self.assertEqual(count, 1)
        ### Start later, end later
        start = self.event.start_time + relativedelta(minutes=5)
        end = self.event.end_time + relativedelta(minutes=5)
        count = Event.objects.overlapping_events(start=start, end=end).count()
        self.assertEqual(count, 1)
        ### Start later, end earlier
        start = self.event.start_time + relativedelta(minutes=5)
        end = self.event.end_time - relativedelta(minutes=5)
        count = Event.objects.overlapping_events(start=start, end=end).count()
        self.assertEqual(count, 1)

    def test_duplicate_save(self):
        self.event.id = None
        self.assertRaises(CollisionException, lambda: self.event.save())

    def test_disable_bulk_insert(self):
        event_list = [self.event, self.event]
        for i in range(0, len(event_list)):
            event_list[i].pk = None
        self.assertRaises(NotImplementedError, lambda: Event.objects.bulk_create(event_list))
    
    def test_no_time_intervall(self):
        e = Event(start_time=datetime.datetime.now(), description='asdf')
        self.assertRaises(ValidationError, lambda: e.save())
    
    def test_disable_update_queryset(self):
        qs = Event.objects.all()
        self.assertRaises(NotImplementedError, lambda: qs.update(start_time=datetime.datetime.now()))