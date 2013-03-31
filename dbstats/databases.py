from django.db import connections


class BaseDatabase(object):
    """
    A database connection that supports the functions we use, like 'explain' and 'get_settings'
    """
    _backend_class = None
    _base_database = None
    _settings_query = None
    _activity_query = None
    _database_options = {
        'connect_timeout': 5,
    }

    def __init__(self, server):
        """
        This class provides a connection to a database and actions against it.

        Using epydoc: http://epydoc.sourceforge.net/manual-epytext.html
        @type server: dbstats.models.Server
        """
        self.model = server
        connections.databases[self.model.api_key] = {
            'ENGINE': self._backend_class,
            'NAME': self._base_database,
            'USER': self.model.username,
            'PASSWORD': self.model.password,
            'HOST': self.model.host,
            'PORT': self.model.port,
            'DATABASE_OPTIONS': self._database_options
        }

    def query(self, statement):
        """Run a given SQL query and return a results as a list of dictionaries"""
        conn = connections[self.model.api_key]
        cursor = conn.cursor()
        cursor.execute(statement)
        # Returns all rows from a cursor as a dict
        desc = cursor.description
        results = [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
        ]
        conn.close()
        return results

    def get_settings(self):
        return self.query(self._settings_query)

    def get_activity(self, database):
        return self.query(self._activity_query.format(database=database))

    def explain(self, statement):
        raise NotImplementedError()


class Postgres(BaseDatabase):
    _backend_class = 'django.db.backends.postgresql_psycopg2'
    _base_database = 'postgres'
    _settings_query = 'select * from pg_settings'
    _activity_query = """
    select usename, case state when 'active' then query end as query,
    query_start as start, current_timestamp - query_start as duration
    from pg_stat_activity where datname = '{database}'
    """

    def get_settings(self):
        settings = super(Postgres, self).get_settings()
        formatted_settings = list()
        for setting in settings:
            formatted_settings.append(
                {'name': setting['name'],
                 'default': setting['boot_val'],
                 'override': setting['setting'] if setting['setting'] != setting['boot_val'] else '',
                 'description': setting['short_desc']}
            )
        return formatted_settings

    def explain(self, statement):
        # add ANALYZE to see the actual runtimes
        plan = self.query(u"EXPLAIN {0}".format(statement))
        return '\n'.join([row['QUERY PLAN'] for row in plan])


class MySQL(BaseDatabase):
    # TODO: finish this implementation
    _backend_class = 'django.db.backends.mysql'
    _base_database = 'information_schema'
    _settings_query = 'SHOW VARIABLES'
    _activity_query = 'select '

    def get_settings(self):
        settings = super(MySQL, self).get_settings()
        formatted_settings = list()
        for setting in settings:
            formatted_settings.append(
                {'name': setting['name'],
                 'default': setting['boot_val'],
                 'override': setting['setting'] if setting['setting'] != setting['boot_val'] else '',
                 'description': setting['short_desc']}
            )
        return formatted_settings
