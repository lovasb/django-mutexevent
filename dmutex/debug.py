

class CollisionException(Exception):
    def __init__(self, start, end, queryset):
        self.start_time = start
        self.end_time = end
        self.qs = queryset
        super(CollisionException, self).__init__()

    def __str__(self):
        return "There are %(count)d overlapping %(model)s(s) in the %(start)s - %(end)s time intervall!" %\
                    {'count': self.qs.count(), 'model': self.qs.model._meta.object_name.lower(), 
                     'start': self.start_time, 'end': self.end_time}