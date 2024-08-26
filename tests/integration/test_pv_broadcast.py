# standard imports
import itertools
from unittest.mock import MagicMock

# third-party imports
import pytest

# webmonchow imports
from webmonchow.pv.broadcast import broadcast, pv_generator, read_contents


def test_broadcast(content_files):
    programmes = read_contents([filepath for filepath in content_files["pv"].values()])
    mock_conn = MagicMock()
    max_items = 40  # Limit the generator to a maximum number of items
    limited_message_gen = itertools.islice(pv_generator(programmes), max_items)
    broadcast(mock_conn, limited_message_gen)
    assert mock_conn.commit.call_count == max_items


if __name__ == "__main__":
    pytest.main([__file__])
