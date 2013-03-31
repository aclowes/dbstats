import hashlib
import sys
import signal
import zmq
import logging
import pytz

from datetime import datetime
from django.core.management.base import BaseCommand

from dbstats.models import Server, Database, SqlStatement, SqlActivity

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('dbstats.server')


class Command(BaseCommand):
#    args = '<arg>'
    help = 'Run server to receive log files'

    def handle(self, *args, **options):
        logger.info('Server starting...')
        logger.info('Press Ctrl+C to stop')
        signal.signal(signal.SIGINT, self.signal_interrupt)

        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.REP)
        self.receiver.bind('tcp://127.0.0.1:1201')

        while True:
            logger.debug(u'Waiting for messages')
            try:
                stats = self.receiver.recv_json()
                logger.debug(u'Received message, length {}'.format(len(stats)))
                self.receiver.send('Thanks')
            except zmq.ZMQError as exc:
                logger.warning(u'Error receiving message: {}'.format(exc))
            else:
                # call handle function
                self.store(stats)

    def store(self, stats):
        """Saves the SQL statement in the database"""
        try:
            server = Server.objects.get(api_key=stats['api_key'])
        except Server.DoesNotExist:
            logger.warning(u'Received stats for unknown API key: {}'.format(stats['api_key']))
            return
        except KeyError:
            logger.warning(u'Received stats with missing API key')
            return

        try:
            for logline in stats['statements']:
                logger.debug(u'    %s' % logline)
                hashed = hashlib.md5(logline['statement']).hexdigest()
                database, created = Database.objects.get_or_create(server=server, name=logline['database'])
                statement, created = SqlStatement.objects.get_or_create(
                    database=database, hashed=hashed, defaults=dict(statement=logline['statement']))
                # 2012-10-30 16:46:11.354 EDT but django expects six millisecond places
                start = datetime.strptime(logline['log_time'][:-4] + '000', '%Y-%m-%d %H:%M:%S.%f')
                start = start.replace(tzinfo=pytz.timezone(logline['log_time'][-3:]))
                activity = SqlActivity(statement=statement, start=start, duration=logline['duration']).save()
        except KeyError as exc:
            logger.warning(u'Received stats with missing key: {}'.format(exc))
        except Exception as exc:
            logger.warning(u'Unexpected exception: {}'.format(exc))

    def signal_interrupt(self, signal, frame):
        """Shutdown signal handler"""
        logger.info('Interrupt received, shutting down')
        if self.receiver:
            self.receiver.close()
            self.receiver = None
            logger.debug('Closed receiver')
        if self.context:
            self.context.destroy()
            self.context = None
            logger.debug('Destroyed context')
        sys.exit(0)
