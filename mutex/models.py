from django.conf import settings
from django.db import models
from django.db.models import Q
from .debug import CollisionException

class MutexModelOptions(object):
    def __init__(self, opts):
        if opts:
            for key, value in opts.__dict__.iteritems():
                setattr(self, key, value)


class MutexModelBase(models.base.ModelBase):
    def __new__(cls, name, bases, attrs):
        new = super(MutexModelBase, cls).__new__(cls, name, bases, attrs)
        meta = attrs.pop('MutexMeta', None)
        setattr(new, '_mutex_meta', MutexModelOptions(meta))
        return new

### Custom queryset, that ignores some updates
class MutexQuerySet(models.query.QuerySet):
    def update(self, **kwargs):
        if 'start_time' in kwargs.keys() or 'end_time' in kwargs.keys():
            raise NotImplementedError("Mutex event start and end time can't be updated via queryset update method. Use object save method instead!")
        return super(MutexQuerySet, self).update(**kwargs)

class MutexManager(models.Manager):
    def get_query_set(self):
        return MutexQuerySet(self.model, using=self._db)

    def bulk_create(self, objs, batch_size=None):
        raise NotImplementedError("Mutex event can't be bulk created!")

    def overlapping_events(self, start, end, obj=None):
        if getattr(settings, 'MUTEX_INTERVALL_TYPE', 'close') == 'open':
            filters = (
                Q(start_time__lt=end), Q(end_time__gt=start)
            )
        else:
            filters = (
                Q(start_time__lte=end), Q(end_time__gte=start) 
            )
        filters2 = {}
        exclude = getattr(self.model._mutex_meta, 'exclude', Q())
        if obj:
            for field in getattr(self.model._mutex_meta, 'collision_fields', []):
                if getattr(obj, field, None) is not None:
                    filters2[field] = getattr(obj, field)
            ## when we modify the event, then exclude that from the queryset
            if obj.pk is not None:
                if len(exclude):
                    exclude = Q(pk=obj.pk) | exclude
                else:
                    exclude = Q(pk=obj.pk)
        return super(MutexManager, self).get_query_set()\
                                        .filter(*filters, **filters2)\
                                        .exclude(*(exclude, ))\
                                        .values_list('id')

class MutexEvent(models.Model):
    __metaclass__ = MutexModelBase

    start_time = models.DateTimeField(blank=False, null=False, db_index=True)
    end_time = models.DateTimeField(blank=False, null=False, db_index=True)
    objects = MutexManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        overlaps = self._default_manager.overlapping_events(start=self.start_time, end=self.end_time, obj=self)
        if overlaps.count():
            raise CollisionException(start=self.start_time, end=self.end_time, queryset=overlaps)
        return super(MutexEvent, self).save(*args, **kwargs)