# standard imports
import json
import os
from unittest import TestCase
from unittest.mock import mock_open, patch

# third-party imports
import pytest
import stomp

# webmonchow imports
from webmonchow.amq.broadcast import (
    broadcast,
    connect_to_broker,
    get_options,
    message_generator,
    read_contents,
    service_content_files,
)


def test_service_content_files():
    result = [os.path.basename(filename) for filename in service_content_files()]
    assert sorted(result) == ["dasmon.json", "pvsd.json", "translation.json"]


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


def test_message_generator():
    data = {
        "queue1": [{"frequency": 1, "message": "msg1"}],
        "queue2": [{"frequency": 2, "message": "msg2"}, {"frequency": 0, "message": "msg3"}],
    }
    gen = message_generator(data)
    assert next(gen) == ("queue1", "msg1")
    assert next(gen) == ("queue2", "msg2")
    assert next(gen) == ("queue2", "msg3")
    assert next(gen) == ("queue1", "msg1")
    assert next(gen) == ("queue1", "msg1")
    assert next(gen) == ("queue2", "msg2")


class TestConnectToBroker(TestCase):
    @patch("stomp.Connection")
    def test_connects_successfully(self, mock_connection):
        mock_conn = mock_connection.return_value
        mock_conn.connect.return_value = mock_conn

        broker = "localhost:61613"
        user = "user"
        password = "password"
        conn = connect_to_broker(broker, user, password)

        self.assertEqual(conn, mock_conn)
        mock_conn.connect.assert_called_once_with(user, password, wait=True)

    def test_fails_and_exceeds_attempts(self):
        broker = "localhost:61613"
        user = "user"
        password = "password"
        with pytest.raises(stomp.exception.ConnectFailedException) as e:
            connect_to_broker(broker, user, password, attempts=2, interval=1.0)
        assert str(e.value) == "Failed to connect to broker after 2 attempts."


def test_broadcast():
    with patch("stomp.Connection", autospec=True) as mock_connection:
        mock_conn = mock_connection.return_value
        message_gen = iter([("queue1", "msg1"), ("queue2", "msg2")])
        with patch("json.dumps", side_effect=lambda x: x):
            broadcast(mock_conn, message_gen)
            mock_conn.send.assert_any_call("queue1", "msg1")
            mock_conn.send.assert_any_call("queue2", "msg2")


def test_get_options_default():
    options = get_options([])
    assert options.user == "icat"
    assert options.password == "icat"
    assert options.broker == "localhost:61613"
    file_names = [os.path.basename(filename) for filename in options.content_files.split(",")]
    assert sorted(file_names) == ["dasmon.json", "pvsd.json", "translation.json"]


def test_get_options():
    options = get_options(
        [
            "--user",
            "user",
            "--password",
            "password",
            "--broker",
            "127.0.0.1",
            "--content-files",
            "file1.json, file2.json",
        ]
    )
    assert options.user == "user"
    assert options.password == "password"
    assert options.broker == "127.0.0.1"
    assert options.content_files == "file1.json, file2.json"


if __name__ == "__main__":
    pytest.main([__file__])
