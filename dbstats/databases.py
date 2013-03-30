from django.db import connections


def get_wrapper(server):
    TYPES = {
        'postgres': Postgres
    }
    if server.type not in TYPES:
        raise RuntimeError('Server type {type} not supported'.format(server))
    return TYPES[server.type](server)


class BaseDatabase(object):
    """
    A database connection that supports the functions we use, like 'explain' and 'get_settings'
    """
    backend = None
    settings_query = None
    base_database = None

    def __init__(self, server):
        self.model = server
        connections.databases[self.model.api_key] = {
            'ENGINE': self.backend,
            'NAME': self.base_database,
            'USER': self.model.username,
            'PASSWORD': self.model.password,
            'HOST': self.model.host,
            'PORT': '5432',
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
        settings = self.query(self.settings_query)
        return self.format_settings(settings)

    def format_settings(self, settings):
        raise NotImplementedError()

    def explain(self, statement):
        raise NotImplementedError()


class Postgres(BaseDatabase):
    backend = 'django.db.backends.postgresql_psycopg2'
    settings_query = 'select * from pg_settings'
    base_database = 'postgres'

    def format_settings(self, settings):
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
    backend = 'django.db.backends.mysql'
    settings_query = 'SHOW VARIABLES'
    base_database = 'information_schema'

    def format_settings(self, settings):
        formatted_settings = list()
        for setting in settings:
            formatted_settings.append(
                {'name': setting['name'],
                 'default': setting['boot_val'],
                 'override': setting['setting'] if setting['setting'] != setting['boot_val'] else '',
                 'description': setting['short_desc']}
            )
        return formatted_settings
