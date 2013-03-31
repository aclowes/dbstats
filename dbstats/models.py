import hashlib
import inspect
import random

from django.db import models

from dbstats import databases


def generate_apikey():
    return hashlib.md5(str(random.random())).hexdigest()


database_types = [(name, name) for name, obj in databases.__dict__.items()
                  if inspect.isclass(obj) and issubclass(obj, databases.BaseDatabase)
                  and obj != databases.BaseDatabase]


class Server(models.Model):
    database_type = models.CharField(max_length=16, choices=database_types)
    api_key = models.CharField(max_length=64, default=generate_apikey, editable=False)
    host = models.CharField(max_length=64)
    port = models.IntegerField()
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=64, blank=True)

    def get_backend(self):
        """@rtype: BaseDatabase"""
        return getattr(databases, self.database_type)(self)

    def __unicode__(self):
        return '{server.host}:{server.port}'.format(server=self)


class Database(models.Model):
    server = models.ForeignKey(Server)
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return u'{db.server} / {db.name}'.format(db=self)


class SqlStatement(models.Model):
    database = models.ForeignKey(Database)
    hashed = models.CharField(max_length=32)
    statement = models.TextField()

    def __unicode__(self):
        return u' '.join(self.statement.split(' ')[:8])


class SqlActivity(models.Model):
    statement = models.ForeignKey(SqlStatement)
    start = models.DateTimeField()
    duration = models.IntegerField(help_text='Statement processing time in milliseconds')

    class Meta:
        verbose_name_plural = 'Sql activity'

    def __unicode__(self):
        return u'{} #{}'.format(self.statement, self.id)


class Statistic(models.Model):
    """
    A disk or memory usage statistic reported by the dbstat agent
    """
    database = models.ForeignKey(Database)
    sampled = models.DateTimeField()
    data = models.TextField()
