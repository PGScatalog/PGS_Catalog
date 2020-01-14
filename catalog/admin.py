from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(Publication)
admin.site.register(Score)
admin.site.register(Cohort)
admin.site.register(Sample)
admin.site.register(SampleSet)
admin.site.register(Performance)
admin.site.register(Metric)
admin.site.register(Demographic)


