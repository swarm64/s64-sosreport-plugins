
from contextlib import contextmanager

import pytest
from psycopg2 import DatabaseError

from plugins.postgresql_alt import PostgreSQLAlt


TEST_CONFIG = [
    ('foo', '1'),
    ('bar', '2'),
    ('foobar', '')
]


TEST_CONFIG_STR = "foo = 1\nbar = 2\nfoobar = ''"


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

def test_get_should_collect_logs(conn):
    conn.fetchall_return_value = (
        ('log_destination', 'stderr'),
        ('logging_collector', 'on')
    )
    should_collect_logs, err = PostgreSQLAlt.get_should_collect_logs(conn)
    assert err is None
    assert should_collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'stderr'),
        ('logging_collector', 'off')
    )
    should_collect_logs, err = PostgreSQLAlt.get_should_collect_logs(conn)
    assert err is None
    assert not should_collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'csvlog'),
        ('logging_collector', 'on')
    )
    should_collect_logs, err = PostgreSQLAlt.get_should_collect_logs(conn)
    assert err is None
    assert should_collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'csvlog'),
        ('logging_collector', 'off')
    )
    should_collect_logs, err = PostgreSQLAlt.get_should_collect_logs(conn)
    assert err is None
    assert not should_collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'csvlog,stderr'),
        ('logging_collector', 'on')
    )
    should_collect_logs, err = PostgreSQLAlt.get_should_collect_logs(conn)
    assert err is None
    assert should_collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'csvlog,stderr'),
        ('logging_collector', 'off')
    )
    should_collect_logs, err = PostgreSQLAlt.get_should_collect_logs(conn)
    assert err is None
    assert not should_collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'syslog'),
        ('logging_collector', 'on')
    )
    should_collect_logs, err = PostgreSQLAlt.get_should_collect_logs(conn)
    assert err is None
    assert not should_collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'syslog'),
        ('logging_collector', 'off')
    )
    should_collect_logs, err = PostgreSQLAlt.get_should_collect_logs(conn)
    assert err is None
    assert not should_collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'syslog,stderr'),
        ('logging_collector', 'on')
    )
    should_collect_logs, err = PostgreSQLAlt.get_should_collect_logs(conn)
    assert err is None
    assert should_collect_logs

    conn.fetchall_return_value = (
        ('log_destination', 'syslog,stderr'),
        ('logging_collector', 'off')
    )
    should_collect_logs, err = PostgreSQLAlt.get_should_collect_logs(conn)
    assert err is None
    assert not should_collect_logs
