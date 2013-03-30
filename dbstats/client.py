import signal, os, sys, re
import time, logging, csv
import zmq

from subprocess import check_output

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('dbstats.client')

WAIT_SECONDS = 5
API_KEY = '2182fcbf214a912c4729286032114b0e'
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 1201

class LogReportingClient(object):
    """Monitors database logs and sends SQL statements to server
    """

    def start(self):
        logger.info('Log file daemon starting...')
        logger.info('Press Ctrl+C to stop')
        signal.signal(signal.SIGINT, self.signal_interrupt)

        logger.info('Connecting to server')
        self.context = zmq.Context()
        self.sender = self.context.socket(zmq.REQ)
        self.sender.connect('tcp://{host}:{port}'.format(host=SERVER_HOST, port=SERVER_PORT))

        self.get_logs()

    def send_stats_to_server(self, lines, outfile):
        stats = dict(api_key=API_KEY, statements=list())
        log_entries = list()
        FIELDS = (
            'log_time', 'user_name', 'database_name', 'process_id', 'connection_from', 'session_id', 'session_line_num',
            'command_tag', 'session_start_time', 'virtual_transaction_id', 'transaction_id', 'error_severity',
            'sql_state_code', 'message', 'detail', 'hint', 'internal_query', 'internal_query_pos', 'context', 'query',
            'query_pos', 'location', 'application_name')
        reader = csv.DictReader(lines, FIELDS)

        # if the logline is a query, send to the server. else record in log file
        for line in reader:
            if line['message'].startswith('duration: '):
                # duration: 7.485 ms  statement: SELECT usecreatedb...
                try:
                    duration, statement = re.match(
                        r'duration: ([\d\.]+) ms  statement: (.+)', line['message'], re.S).group(1, 2)
                    entry = {
                        'log_time': line['log_time'],
                        'database': line['database_name'],
                        'statement': statement,
                        'duration': duration,
                        }
                    stats['statements'].append(entry)
                except AttributeError as exc:
                    pass # no match...
            else:
                log_entries.append(u'[{log_time}] {error_severity}: {message}\n'.format(**line))

        logger.debug('Sending {} lines to server'.format(len(stats)))
        self.sender.send_json(stats)
        response = self.sender.recv()
        logger.debug('Received response: {}'.format(response))
        outfile.writelines(log_entries)
        logger.debug('Wrote {} lines to log file'.format(len(log_entries)))

    def signal_interrupt(self, signal, frame):
        """handle shutdown"""
        logger.info('Interrupt received, shutting down')
        if self.sender:
            self.sender.close()
            self.sender = None
            logger.debug('Closed sender')
        if self.context:
            self.context.destroy()
            self.context = None
            logger.debug('Destroyed context')
        sys.exit(0)

    def get_logs(self):
        """
        Monitors postgresql log files

        Requirements:
        - listening on default local unix socket: unix_socket_directory = '/var/pgsql_socket
        - local connections are trusted in pg_hba.conf
        - log_destination = 'csvlog'
        - log_min_duration_statement = 0 or positive number as desired
        """
        # connect to postgres and get the current settings
        table = check_output(['psql', 'postgres', '-A', '-c', 'select * from pg_settings;'])
        rows = table.split('\n')
        settings = dict()
        for row in rows[1:-2]:
            columns = row.split('|')
            settings[columns[0]] = columns[1]
            #update pg_settings set setting = '' where name = '';

        # monitor new file that are frequently rotated
        if settings['log_directory'][0] == '/':
            log_directory = settings['log_directory']
        else:
            log_directory = os.path.join(settings['data_directory'], settings['log_directory'])

        def get_filenames():
            files = list()
            for file in os.listdir(log_directory):
                fullpath = os.path.join(log_directory, file)
                if os.path.isfile(fullpath) and re.search(r'\.csv$', file):
                    files.append(fullpath)
            if not files:
                logger.warning('No log files found in directory {}'.format(log_directory))
            return files

        def get_logfiles(filename):
            logfile = file(filename, 'rb')
            logger.info('Found new filename %s' % logfile.name)
            outfile = file(logfile.name.replace('.csv', '.log'), 'ab')
            return logfile, outfile

        # list of files in the directory ending in csv
        files = get_filenames()
        logfile, outfile = None, None

        while True:
            if not files and not logfile:
                logger.debug('Waiting {} seconds for files to appear in log directory'.format(WAIT_SECONDS))
                time.sleep(WAIT_SECONDS)
                continue
            if not logfile or logfile.closed:
                logfile, outfile = get_logfiles(files.pop(0))

            where = logfile.tell()
            lines = logfile.readlines(1024 * 1024)
            if lines:
                self.send_stats_to_server(lines, outfile)
            else:
                # close this file if a newer file exists
                if files or len(get_filenames()) > 1:
                    logfile.close(), outfile.close()
                    # TODO option to delete
                    # rename the old log file, so we don't reload it.
                    os.rename(logfile.name, logfile.name + '.bak')
                else:
                    logger.debug('Waiting {} seconds for next poll'.format(WAIT_SECONDS))
                    time.sleep(WAIT_SECONDS)
                    logfile.seek(where)


if __name__ == "__main__":
    LogReportingClient().start()
