# -*- coding: utf8 -*-

from sos.report.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin
from typing import List, Tuple

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
    def do_connect(cls, dsn: str) -> object:
        try:
            conn = psycopg2.connect(dsn=dsn)
        except psycopg2.Error as err:
            return (None, err)

        return (conn, None)

    @classmethod
    def get_config(cls, conn: object) -> List[Tuple[str, str]]:
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
