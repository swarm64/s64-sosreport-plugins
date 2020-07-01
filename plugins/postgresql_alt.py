# -*- coding: utf8 -*-

from sos.report.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin
from typing import Dict, List, Tuple

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
    def _do_query(cls, conn: object, sql: str) -> Tuple[str, str]:
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                return (cur.fetchall(), None)
        except psycopg2.Error as err:
            return (None, err)

    @classmethod
    def get_config(cls, conn: object) -> List[Tuple[str, str]]:
        sql = 'SELECT name, setting FROM pg_settings ORDER BY name ASC'
        return cls._do_query(conn, sql)

    @classmethod
    def config_to_string(cls, config: List[Tuple[str, str]]) -> str:
        def normalize_string(s):
            return s if s else "''"

        return '\n'.join([f'{key} = {normalize_string(value)}' for key, value in config])

    @classmethod
    def get_s64_license(cls, conn: object) -> Tuple[Dict, str]:
        sql = 'SELECT * FROM swarm64da.show_license()'
        license_info, err = cls._do_query(conn, sql)
        if err:
            return (None, err)

        if not license_info:
            return ({}, err)

        license_info = license_info[0]
        return ({
            'type': license_info[0],
            'start': license_info[1],
            'expiry': license_info[2],
            'customer': license_info[3]
        }, err)

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

        license_info, error = PostgreSQLAlt.get_s64_license(conn)
        if error:
            self.write_output(f'Could not get Swarm64 license: {error}')
        self.write_output(f'Swarm64 license info: {str(license_info)}')
