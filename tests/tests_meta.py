import datetime
from copy import deepcopy
from dateutil.relativedelta import relativedelta
from .models import Booking, Room, RequestedBooking
from mutex.debug import CollisionException
from django.test import TestCase


class MetaClassOptions(TestCase):
    def setUp(self):
        now = datetime.datetime.now()
        self.room = Room.objects.create(name='Room')
        self.living_room = Room.objects.create(name='Living room', can_parallel=True)
        self.booking1 = Booking(start_time=datetime.datetime.now(), 
                                end_time=now + relativedelta(days=1), 
                                room=self.room)
        self.booking1.save()
        self.booking2 = Booking(start_time=datetime.datetime.now(), 
                                end_time=now + relativedelta(days=1), 
                                room=self.living_room)
        self.booking2.save()

    def test_duplicate_save(self):
        ### Normal room can't be re-booked
        self.booking1.id = None
        self.assertRaises(CollisionException, lambda: self.booking1.save())
        ### Living room can be re-booked
        booking3 = deepcopy(self.booking2)
        booking3.pk = None
        booking3.save()
        self.assertEqual(booking3.start_time, self.booking2.start_time)
        self.assertEqual(booking3.end_time, self.booking2.end_time)

    def test_delete(self):
        self.booking1.deleted_at = datetime.datetime.now()
        self.booking1.save()
        booking3 = deepcopy(self.booking1)
        booking3.id = None
        booking3.save()
        self.assertEqual(booking3.start_time, self.booking1.start_time)
        self.assertEqual(booking3.end_time, self.booking1.end_time)
        self.assertEqual(booking3.room, self.booking1.room)

    def test_collision_is_blank(self):
        start = datetime.datetime.now()
        end = start + relativedelta(days=1)
        rb1 = RequestedBooking(request='room', start_time=start, end_time=end)
        rb1.save()
        rb2 = deepcopy(rb1)
        rb2.pk = None
        rb2.save()
        self.assertEqual(rb1.start_time, rb2.start_time)
        self.assertEqual(rb1.end_time, rb2.end_time)
        self.assertNotEqual(rb1.pk, rb2.pk)
        rb1.room = Room.objects.get(pk=1)
        rb2.room = Room.objects.get(pk=1)
        rb1.save()
        self.assertRaises(CollisionException, lambda: rb2.save())