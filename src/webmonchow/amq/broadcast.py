# standard imports
import argparse
import glob
import json
import math
import os
import time
from typing import List

# third party imports
import stomp


def service_content_files() -> List[str]:
    r"""Absolute paths to all content *.json files under directory services/."""
    services_dir = os.path.join(os.path.dirname(__file__), "services")
    files = glob.glob(os.path.join(services_dir, "*.json"))
    absolute_paths = [os.path.abspath(file) for file in files]
    return absolute_paths


def read_contents(filenames: List[str]):
    """
    Reads and combines JSON data from multiple content files.

    Parameters
    ----------
    filenames : List[str]
        A list of file paths to JSON files.

    Returns
    -------
    dict
        A dictionary containing the combined data from all JSON files.
    """
    data = {}
    for filename in filenames:
        print(f"Loading {filename}")
        with open(filename) as f:
            data.update(json.load(f))
    return data


def message_generator(data):
    """
    Generates messages at specified intervals based on their assigned frequency.

    Parameters
    ----------
    data : dict
        A dictionary where each key is a destination (queue or topic) and each value is a list of programmes.
        Each programme is a dictionary with 'frequency' and 'message' keys.
        The units of 'frequency' are seconds, meaning the time interval between two messages.

    Yields
    ------
    tuple
        A tuple containing the destination queue or topic, and message to send.
    """
    time_step = 0.5  # in seconds. Maximum frequency for any message to be sent
    count = 0
    while True:
        for queue_or_topic, programmes in data.items():
            for programme in programmes:
                yield_tuple = queue_or_topic, programme["message"]
                skip_counts = math.ceil(programme["frequency"] / time_step)
                if skip_counts == 0:  # only if frequency is 0
                    if count == 0:
                        yield yield_tuple
                elif count % skip_counts == 0:
                    yield yield_tuple
        time.sleep(time_step)
        count += 1


def broadcast(connection, message_gen):
    """
    Sends messages to specified AMQ queues or topics using an established connection.

    Parameters
    ----------
    connection : stomp.Connection
        An active connection to the AMQ message broker.
    message_gen : generator
        A python generator that yields tuples containing the destination queue or topic and the message to be sent.
        The generator yields messages at specified intervals based on their assigned frequency.
    """
    for queue_or_topic, message in message_gen:
        print(f"Sending {message} to {queue_or_topic}")
        connection.send(queue_or_topic, json.dumps(message))


def connect_to_broker(broker, user, password):
    """
    Creates and returns a connection to an AMQ broker.

    Parameters
    ----------
    broker : str
        The AMQ broker address in the format 'host:port'.
    user : str
        The username for the connection.
    password : str
        The password for the connection.

    Returns
    -------
    stomp.Connection
        An established connection.
    """
    conn = stomp.Connection(
        host_and_ports=[
            tuple(broker.split(":")),
        ]
    )
    conn.connect(user, password, wait=True)
    return conn


def get_options(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", "-u", dest="user", default=os.getenv("ICAT_USER", "icat"))
    parser.add_argument("--password", "-p", dest="password", default=os.getenv("ICAT_PASS", "icat"))
    parser.add_argument("--broker", "-b", dest="broker", default=os.getenv("BROKER", "localhost:61613"))
    parser.add_argument(
        "--content-files",
        "-m",
        help="List of content files to broadcast, separated by comma.",
        dest="content_files" "",
        default=service_content_files(),
    )
    options = parser.parse_args(argv)
    return options


def main(argv=None):
    options = get_options(argv)
    data = read_contents([f.strip() for f in options.content_files.split(",")])
    connection = connect_to_broker(options.broker, options.user, options.password)
    broadcast(connection, message_generator(data))


if __name__ == "__main__":
    main()
