# standard imports
import json
import os
from unittest.mock import MagicMock, mock_open, patch

# third-party imports
import psycopg2
import pytest

# webmonchow imports
from webmonchow.pv.broadcast import (
    broadcast,
    connect_to_database,
    get_options,
    pv_generator,
    read_contents,
    service_content_files,
)


def test_service_content_files():
    result = [os.path.basename(filename) for filename in service_content_files()]
    assert result == ["dasmon.json"]


def test_read_contents():
    mock_files = {"/fake/dir/file1.json": '{"key1": "value1"}', "/fake/dir/file2.json": '{"key2": "value2"}'}

    m = mock_open()

    # Adding side_effect to mock open to include the 'name' attribute.
    def mock_file_open(file, *args, **kwargs):
        file_object = m(file, *args, **kwargs)
        file_object.name = file
        return file_object

    with patch("builtins.open", mock_file_open):
        with patch("json.load", side_effect=lambda f: json.loads(mock_files[f.name])):
            result = read_contents(["/fake/dir/file1.json", "/fake/dir/file2.json"])
            assert result == {"key1": "value1", "key2": "value2"}


def test_pv_generator():
    test_data = {
        "pvUpdate": [
            {"frequency": 0, "instrument": "TEST", "name": "testPV1", "function": "100"},
            {"frequency": 1, "instrument": "TEST", "name": "testPV2", "function": "{x}"},
        ],
        "pvStringUpdate": [{"frequency": 0, "instrument": "TEST", "name": "testPV3", "function": "'string {x}'"}],
    }
    pv_gen = pv_generator(test_data)
    assert next(pv_gen) == ("pvUpdate", "TEST", "testPV1", 100)
    assert next(pv_gen) == ("pvUpdate", "TEST", "testPV2", 0)
    assert next(pv_gen) == ("pvStringUpdate", "TEST", "testPV3", "string 0.0")
    assert next(pv_gen) == ("pvUpdate", "TEST", "testPV2", 1.0)
    assert next(pv_gen) == ("pvUpdate", "TEST", "testPV2", 2.0)


@patch("psycopg2.connect")
def test_connect_to_database(mock_psycopg2_connect):
    connect_to_database("database", "user", "password", "host", "port")
    mock_psycopg2_connect.assert_called_once_with(
        database="database", host="host", password="password", port="port", user="user"
    )


def test_connect_to_database_fails():
    with pytest.raises(psycopg2.OperationalError) as e:
        connect_to_database("database", "user", "password", "host", "port", attempts=2, interval=1.0)
    assert str(e.value) == "Failed to connect to database after 2 attempts."


@patch("time.time")
def test_broadcast(mock_time):
    mock_time.return_value = 123456
    mock_conn = MagicMock()
    pv_gen = [("pvUpdate", "TEST", "testPV1", 100), ("pvUpdate", "TEST", "testPV2", 1)]

    broadcast(mock_conn, pv_gen)

    mock_conn.cursor.assert_called_once()
    mock_conn.commit.assert_called()
    assert mock_conn.commit.call_count == 2

    mock_conn.cursor().execute.assert_called()
    assert mock_conn.cursor().execute.call_count == 2
    mock_conn.cursor().execute.assert_called_with(
        "SELECT * FROM pvUpdate(%s, %s, %s, %s, %s)", ["TEST", "testPV2", 1, 0, 123456]
    )


def test_get_options_default():
    options = get_options([])
    assert options.user == "postgres"
    assert options.password == "postgres"
    assert options.host == "localhost"
    assert options.port == "5432"
    assert options.database == "workflow"
    assert os.path.basename(options.pv_files) == "dasmon.json"


def test_get_options():
    options = get_options(
        [
            "--user",
            "user",
            "--password",
            "password",
            "--host",
            "127.0.0.1",
            "--port",
            "42",
            "--database-name",
            "db",
            "--pv-files",
            "file.json",
        ]
    )
    assert options.user == "user"
    assert options.password == "password"
    assert options.host == "127.0.0.1"
    assert options.port == "42"
    assert options.database == "db"
    assert options.pv_files == "file.json"


if __name__ == "__main__":
    pytest.main([__file__])
