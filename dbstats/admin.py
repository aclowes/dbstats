from django.contrib import admin

from dbstats import models

admin.site.register(models.Server)
admin.site.register(models.Database)
admin.site.register(models.SqlStatement)
admin.site.register(models.SqlActivity)
admin.site.register(models.Statistic)
