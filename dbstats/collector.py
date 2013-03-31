import hashlib
import logging
import re

from dbstats.models import Database, SqlStatement, SqlActivity

logger = logging.getLogger('dbstats.server')


def check_stats():
    """
    This function attempts to connect to each database and get the currently running queries
    """

    for database in Database.objects.all():
        logger.debug(u'Checking activity on %s' % database)
        backend = database.server.get_backend()
        active_queries = backend.get_activity(database.name)

        for query in active_queries:
            # strip the query of the parameters, so fewer queries are 'unique'
            stripped_query = re.sub(r'', "''", query)
            logger.debug(u'    %s' % stripped_query[:200])

            # save the statement text if it doesn't already exist
            hashed = hashlib.md5(stripped_query).hexdigest()
            statement, created = SqlStatement.objects.get_or_create(
                database=database, hashed=hashed, defaults=dict(statement=stripped_query))

            # save a smaller record of the activity
            activity = SqlActivity(statement=statement, start=start, duration=logline['duration']).save()
