# -*- coding: utf8 -*-

import os

from shlex import split as shlex_split
from sos.report.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin
from subprocess import check_output, CalledProcessError
from typing import List, Optional, Tuple

import psycopg2

DEFAULT_DSN = 'postgresql://postgres@localhost/postgres'


class LoggingInfo:
    def __init__(self, collect_logs, log_dir, data_dir):
        self.collect_logs = collect_logs
        self.log_dir = log_dir
        self.data_dir = data_dir


class PostgreSQLAlt(Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin):
    """PostgreSQL alternative collection plugin"""
    plugin_name = "postgresql_alt"
    requires_root = False
    short_desc = 'PostgreSQL alternative collection plugin'

    option_list = [
        ('dsn', 'The PostgreSQL DSN to collect information from.', '', DEFAULT_DSN),
        ('container_id', 'The docker container id where PostgreSQL runs in.', '', '')
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
    def get_logging_info(cls, conn: object) -> Tuple[LoggingInfo, Optional[Exception]]:
        logging_info = LoggingInfo(False, '', '')
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT name, setting
                    FROM pg_settings
                    WHERE name IN (
                        'log_destination'
                      , 'logging_collector'
                      , 'log_directory'
                      , 'data_directory'
                    )''')
                logging_config = cur.fetchall()
                logging_config = {key:value for key, value in logging_config}

                log_destinations = logging_config['log_destination'].split(',')
                logging_collector = logging_config['logging_collector']

                logging_info.log_dir = logging_config['log_directory']
                logging_info.data_dir = logging_config['data_directory']
        except psycopg2.Error as err:
            return (logging_info, err)

        except KeyError as err:
            return (logging_info, err)

        if any(item in ['stderr', 'csvlog'] for item in log_destinations):
            if logging_collector == 'on':
                logging_info.collect_logs = True

        return (logging_info, None)

    @classmethod
    def docker_get_data_dir_host(cls, container_id: str, pg_data_dir: str) -> Tuple[str, Optional[Exception]]:
        inspect_cmd  = "docker inspect -f "
        inspect_cmd += "'{{ range .Mounts }}{{ println .Destination .Source }}{{ end }}' "
        inspect_cmd += container_id

        try:
            docker_mounts = check_output(shlex_split(inspect_cmd), universal_newlines=True)
            docker_mounts = docker_mounts.split('\n')
            data_dir = [mount.split(' ')[1] for mount in docker_mounts if pg_data_dir in mount][1]

        except CalledProcessError as err:
            return ('', err)

        except IndexError as err:
            return ('', err)

        return (data_dir, None)

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

        logging_info, error = PostgreSQLAlt.get_logging_info(conn)
        if error:
            self.write_output(f'Could not get log collection info: {error}')
            return

        container_id = self.get_option('container_id')
        if logging_info.collect_logs and container_id:
            data_dir_host = PostgreSQLAlt.docker_get_data_dir_host(container_id, logging_info.data_dir)
            log_dir_host = os.path.join(data_dir_host, logging_info.log_dir, '*')
            self.add_copy_spec(log_dir_host)
