import hashlib
import random

from django.db import models

def generate_apikey():
    return hashlib.md5(str(random.random())).hexdigest()


class Server(models.Model):
    DB_TYPES = (
        ('postgres', 'PostgreSQL'),
        #        ('oracle', 'Oracle'),
        #        ('sqlite', 'SQLite'),
        #        ('mysql', 'MySQL'),
        )
    #    type = models.CharField(max_length=16, choices=DB_TYPES)
    api_key = models.CharField(max_length=64, auto_created=True, default=generate_apikey)
    host = models.CharField(max_length=64)
    #    port = models.IntegerField()
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=64, blank=True)

    def __unicode__(self):
        return self.host


class Database(models.Model):
    server = models.ForeignKey(Server)
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return u'{db.server} / {db.name}'.format(db=self)


class SqlStatement(models.Model):
    database = models.ForeignKey(Database)
    hash = models.CharField(max_length=32)
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
    database = models.ForeignKey(Database)
    sampled = models.DateTimeField()
    data = models.TextField()
