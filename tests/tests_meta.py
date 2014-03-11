import datetime
from copy import deepcopy
from dateutil.relativedelta import relativedelta
from .models import Booking, Room
from mutex.debug import CollisionException


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
