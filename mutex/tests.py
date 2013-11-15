#encoding: utf8
import datetime
from dateutil.relativedelta import relativedelta
from mutex.models import MutexEvent
from django.test import TestCase
from django.db import models
from django.db.models import Q
from mutex.debug import CollisionException
from django.core.exceptions import ValidationError
from mutex.models import MutexQuerySet

class Booking(MutexEvent):
    room = models.CharField(max_length=255)


class MutextTest(TestCase):
    def setUp(self):
        now = datetime.datetime.now()
        self.booking1 = Booking(start_time=datetime.datetime.now(), 
                                end_time=now + relativedelta(days=1), 
                                room='Room 1')
        self.booking1.save()
        #print self.booking1._mutex_exclude

    def test_queryset_retval(self):
        assert isinstance(Booking.objects.all(), MutexQuerySet)

    def test_detect_overlapping(self):
        ### Start and end at the same time
        start = self.booking1.start_time
        end = self.booking1.end_time
        count = Booking.objects.overlapping_events(start=start, end=end).count()
        self.assertEqual(count, 1)
        ### Start earlier and ends later
        start = self.booking1.start_time - relativedelta(minutes=1)
        end = self.booking1.end_time + relativedelta(minutes=1)
        count = Booking.objects.overlapping_events(start=start, end=end).count()
        self.assertEqual(count, 1)
        ### Start earlier, end earlier
        start = self.booking1.start_time - relativedelta(minutes=1)
        end = self.booking1.end_time - relativedelta(minutes=1)
        count = Booking.objects.overlapping_events(start=start, end=end).count()
        self.assertEqual(count, 1)
        ### Start later, end later
        start = self.booking1.start_time + relativedelta(minutes=1)
        end = self.booking1.end_time + relativedelta(minutes=1)
        count = Booking.objects.overlapping_events(start=start, end=end).count()
        self.assertEqual(count, 1)
        ### Start later, end earlier
        start = self.booking1.start_time + relativedelta(minutes=1)
        end = self.booking1.end_time - relativedelta(minutes=1)
        count = Booking.objects.overlapping_events(start=start, end=end).count()
        self.assertEqual(count, 1)

    def test_duplicate_save(self):
        try:
            self.booking1.id = None
            self.booking1.save()
            self.assertEqual(1, 0)
        except CollisionException as e:
            print str(e)
            self.assertEqual(1, 1)

    def test_update_intervall(self):
        s =  self.booking1.start_time
        self.booking1.start_time = datetime.datetime.now()
        self.booking1.save()
        self.assertNotEqual(s, self.booking1.start_time)
        self.assertEqual(Booking.objects.count(), 1)


    def test_disable_bulk_insert(self):
        event_list = [self.booking1, self.booking1]
        for i in range(0, len(event_list)):
            event_list[i].pk = None
        try:
            Booking.objects.bulk_create(event_list)
            self.assertEqual(0, 1)
        except NotImplementedError:
            self.assertEqual(1, 1)

    def test_no_time_intervall(self):
        b = Booking(start_time=datetime.datetime.now(), room='Room 2')
        try:
            b.save()
            self.assertEqual(1, 0)
        except ValidationError:
            self.assertEqual(1, 1)

    def test_disable_update_intervall(self):
        count = Booking.objects.all().update(room='Room 3')
        self.assertEqual(count, 1)
        try:
            count = Booking.objects.all().update(start_time=datetime.datetime.now())
            self.assertEqual(count, 0)
        except NotImplementedError:
            self.assertEqual(1, 1)

##################################### advanced functionality
class Room(models.Model):
    name = models.CharField(max_length=255)
    can_parallel = models.BooleanField(default=False, editable=False)

class Booking2(MutexEvent):
    room = models.ForeignKey(Room)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class MutexMeta:
        collision_fields = ['room']
        exclude = Q(room__can_parallel=True) | Q(deleted_at__isnull=False)

class MutextTest2(TestCase):
    def setUp(self):
        now = datetime.datetime.now()
        self.room = Room.objects.create(name='Room1') ## TODO
        self.living_room = Room.objects.create(name='Living room', can_parallel=True)
        self.booking1 = Booking2(start_time=datetime.datetime.now(), 
                                 end_time=now + relativedelta(days=1), 
                                 room=self.room)
        self.booking1.save()
        self.booking2 = Booking2(start_time=datetime.datetime.now(), 
                                 end_time=now + relativedelta(days=1), 
                                 room=self.living_room)
        self.booking2.save()
        #print self.booking1._mutex_exclude

    def test_duplicate_save(self):
        ### Normal room can't be re-booked
        try:
            self.booking1.id = None
            self.booking1.save()
            self.assertEqual(1, 0)
        except CollisionException as e:
            print str(e)
            self.assertEqual(1, 1)
        ### Living room can be re-booked
        try:
            self.booking2.id = None
            self.booking2.save()
            self.assertEqual(True, True)
        except CollisionException as e:
            self.assertEqual(True, False)

    def test_delete(self):
        self.booking1.deleted_at = datetime.datetime.now()
        #or... Booking2.objects.filter(pk=self.booking1.pk).update(deleted_at=datetime.datetime.now())
        self.booking1.save()
        try:
            self.booking1.id = None
            print self.booking1.deleted_at
            self.booking1.save()
            self.assertEqual(1, 1)
        except CollisionException as e:
            self.assertEqual(1, 0)
