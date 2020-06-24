# -*- coding: utf8 -*-

from sos.report.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin
from typing import List, Optional, Tuple

import psycopg2

DEFAULT_DSN = 'postgresql://postgres@localhost/postgres'

class PostgreSQLAlt(Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin):
    """PostgreSQL alternative collection plugin"""
    plugin_name = "postgresql_alt"
    requires_root = False
    short_desc = 'PostgreSQL alternative collection plugin'

    option_list = [
        ('dsn', 'The PostgreSQL DSN to collect information from.', '', DEFAULT_DSN)
    ]

    @classmethod
    def do_connect(cls, dsn: str) -> Tuple[object, Optional[Exception]]:
        try:
            conn = psycopg2.connect(dsn=dsn)
        except psycopg2.Error as err:
            return (None, err)

        return (conn, None)

    @classmethod
    def get_config(cls, conn: object) -> Tuple[List[Tuple[str, str]], Optional[Exception]]:
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT name, setting FROM pg_settings ORDER BY name ASC')
                config = cur.fetchall()
        except psycopg2.Error as err:
            return (None, err)

        return (config, None)

    @classmethod
    def config_to_string(cls, config: List[Tuple[str, str]]) -> str:
        def normalize_string(s):
            return s if s else "''"

        return '\n'.join([f'{key} = {normalize_string(value)}' for key, value in config])

    @classmethod
    def get_should_collect_logs(cls, conn: object) -> Tuple[bool, Optional[Exception]]:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT name, setting
                    FROM pg_settings
                    WHERE name IN (
                      'log_destination',
                      'logging_collector'
                    )
                   ''')
                logging_config = cur.fetchall()
                logging_config = {key:value for key, value in logging_config}

                log_destinations = logging_config['log_destination'].split(',')
                logging_collector = logging_config['logging_collector']
        except psycopg2.Error as err:
            return (False, err)

        except KeyError as err:
            return (False, err)

        if any(item in ['stderr', 'csvlog'] for item in log_destinations):
            return (logging_collector == 'on', None)

        return (False, None)

    def write_output(self, output):
        self.add_string_as_file(output, 'postgresql.conf')

    def setup(self):
        dsn = self.get_option('dsn')
        conn, error = PostgreSQLAlt.do_connect(dsn)
        if error:
            self.write_output(f'Could not connect to PostgreSQL to get config: {error}')
            return

        config, error = PostgreSQLAlt.get_config(conn)
        if error:
            self.write_output(f'Could not get PostgreSQL config: {error}')
            return

        config_str = PostgreSQLAlt.config_to_string(config)
        self.write_output(config_str)

        if PostgreSQLAlt.get_should_collect_logs(conn):
            pass
