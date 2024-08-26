# standard imports
import itertools
from unittest.mock import patch

# third-party imports
import pytest

# webmonchow imports
from webmonchow.amq.broadcast import broadcast, message_generator, read_contents


def test_broadcast(content_files):
    programmes = read_contents([filepath for filepath in content_files["amq"].values()])
    with patch("stomp.Connection", autospec=True) as mock_connection:
        mock_conn = mock_connection.return_value
        max_items = 40  # Limit the generator to a maximum number of items
        limited_message_gen = itertools.islice(message_generator(programmes), max_items)
        broadcast(mock_conn, limited_message_gen)
        assert mock_conn.send.call_count == max_items


if __name__ == "__main__":
    pytest.main([__file__])
