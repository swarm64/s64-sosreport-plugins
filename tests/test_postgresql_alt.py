
import subprocess

from contextlib import contextmanager

import pytest

from psycopg2 import DatabaseError
from testfixtures.popen import MockPopen, PopenBehaviour

from plugins.postgresql_alt import PostgreSQLAlt


TEST_CONFIG = [
    ('foo', '1'),
    ('bar', '2'),
    ('foobar', '')
]


TEST_CONFIG_STR = "foo = 1\nbar = 2\nfoobar = ''"

DOCKER_OUTPUT = '\n'.join([
    '/var/lib/postgresql/data /var/lib/docker/volumes/8abf2b00c0f5183343805341d6e27d8c3e4155b2316e1a4925177e2c54e12efc/_data',
    '/sys/class/fpga/intel-fpga-dev.0/intel-fpga-port.0 /sys/class/fpga/intel-fpga-dev.0/intel-fpga-port.0',
    '/data /mnt/storage/the_land_where_the_data_lives',
    '/init.sh /root/mitch/s64da-compose/init.sh'
])

@pytest.fixture
def conn(mocker):
    class ConnFixture:
        def __init__(self):
            self.fetchall_return_value = []
            self.fetchall_side_effect = None

        @contextmanager
        def cursor(self):
            cursor = mocker.Mock()
            cursor.fetchall = mocker.Mock(
                return_value=self.fetchall_return_value,
                side_effect=self.fetchall_side_effect)
            try:
                yield cursor
            finally:
                pass

    return ConnFixture()


def test_connect_ok(mocker):
    mocker.patch('psycopg2.connect')
    conn, err = PostgreSQLAlt.do_connect('some_valid_dsn')
    assert conn is not None
    assert err is None

def test_connect_err(mocker):
    mocker.patch('psycopg2.connect', side_effect=DatabaseError('DSN invalid'))
    conn, err = PostgreSQLAlt.do_connect('some_invalid_dsn')
    assert conn is None
    assert err is not None

def test_get_config_ok(conn):
    conn.fetchall_return_value = TEST_CONFIG
    config, err = PostgreSQLAlt.get_config(conn)
    assert config == TEST_CONFIG
    assert err is None

def test_get_config_err(conn):
    conn.fetchall_side_effect = DatabaseError('Something went wrong')
    config, err = PostgreSQLAlt.get_config(conn)
    assert config is None
    assert err is not None

def test_config_to_string():
    config_str = PostgreSQLAlt.config_to_string(TEST_CONFIG)
    assert config_str == TEST_CONFIG_STR

def test_get_logging_info(conn):
    conn.fetchall_return_value = (
        ('log_directory', 'foobar'),
        ('log_destination', 'stderr'),
        ('data_directory', 'fancy'),
        ('logging_collector', 'on')
    )
    logging_info, err = PostgreSQLAlt.get_logging_info(conn)
    assert err is None
    assert logging_info.log_dir == 'foobar'
    assert logging_info.data_dir == 'fancy'
    assert logging_info.collect_logs

    conn.fetchall_return_value = (
        ('log_directory', 'foobar'),
        ('data_directory', 'fancy'),
        ('log_destination', 'stderr'),
        ('logging_collector', 'off')
    )
    logging_info, err = PostgreSQLAlt.get_logging_info(conn)
    assert err is None
    assert logging_info.log_dir == 'foobar'
    assert logging_info.data_dir == 'fancy'
    assert not logging_info.collect_logs

    conn.fetchall_return_value = (
        ('log_directory', 'foobar'),
        ('log_destination', 'csvlog'),
        ('data_directory', 'fancy'),
        ('logging_collector', 'on')
    )
    logging_info, err = PostgreSQLAlt.get_logging_info(conn)
    assert err is None
    assert logging_info.log_dir == 'foobar'
    assert logging_info.data_dir == 'fancy'
    assert logging_info.collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'csvlog'),
        ('log_directory', 'foobar'),
        ('logging_collector', 'off'),
        ('data_directory', 'fancy')
    )
    logging_info, err = PostgreSQLAlt.get_logging_info(conn)
    assert err is None
    assert logging_info.log_dir == 'foobar'
    assert logging_info.data_dir == 'fancy'
    assert not logging_info.collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'csvlog,stderr'),
        ('data_directory', 'fancy'),
        ('log_directory', 'foobar'),
        ('logging_collector', 'on')
    )
    logging_info, err = PostgreSQLAlt.get_logging_info(conn)
    assert err is None
    assert logging_info.log_dir == 'foobar'
    assert logging_info.data_dir == 'fancy'
    assert logging_info.collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'csvlog,stderr'),
        ('logging_collector', 'off'),
        ('data_directory', 'fancy'),
        ('log_directory', 'foobar')
    )
    logging_info, err = PostgreSQLAlt.get_logging_info(conn)
    assert err is None
    assert logging_info.log_dir == 'foobar'
    assert logging_info.data_dir == 'fancy'
    assert not logging_info.collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'syslog'),
        ('data_directory', 'fancy'),
        ('logging_collector', 'on'),
        ('log_directory', 'foobar')
    )
    logging_info, err = PostgreSQLAlt.get_logging_info(conn)
    assert err is None
    assert logging_info.log_dir == 'foobar'
    assert logging_info.data_dir == 'fancy'
    assert not logging_info.collect_logs

    conn.fetchall_return_value = (
        ('log_directory', 'foobar'),
        ('log_destination', 'syslog'),
        ('data_directory', 'fancy'),
        ('logging_collector', 'off')
    )
    logging_info, err = PostgreSQLAlt.get_logging_info(conn)
    assert err is None
    assert logging_info.log_dir == 'foobar'
    assert logging_info.data_dir == 'fancy'
    assert not logging_info.collect_logs

    conn.fetchall_return_value = (
        ('data_directory', 'fancy'),
        ('log_destination', 'syslog,stderr'),
        ('log_directory', 'foobar'),
        ('logging_collector', 'on')
    )
    logging_info, err = PostgreSQLAlt.get_logging_info(conn)
    assert err is None
    assert logging_info.log_dir == 'foobar'
    assert logging_info.data_dir == 'fancy'
    assert logging_info.collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'syslog,stderr'),
        ('log_directory', 'foobar'),
        ('data_directory', 'fancy'),
        ('logging_collector', 'off')
    )
    logging_info, err = PostgreSQLAlt.get_logging_info(conn)
    assert err is None
    assert logging_info.log_dir == 'foobar'
    assert logging_info.data_dir == 'fancy'
    assert not logging_info.collect_logs

def test_docker_get_data_dir_host(mocker):
    popen_mock = MockPopen()
    popen_mock.set_default(stdout=DOCKER_OUTPUT.encode('utf-8'))
    mocker.patch('subprocess.Popen', new=popen_mock)

    data_dir_host, err = PostgreSQLAlt.docker_get_data_dir_host('foobar', '/data')
    assert err is None
    assert data_dir_host == '/mnt/storage/the_land_where_the_data_lives'
