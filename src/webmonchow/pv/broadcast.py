# standard imports
import argparse
import glob
import json
import math  # noqa: F401
import os
import random  # noqa: F401
import time
from typing import List

# third party imports
import psycopg2


def service_content_files():
    r"""Absolute paths to all content *.yml files under directory services/."""
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


def pv_generator(data):
    """
    Generates process variable (PV) data at specified intervals based on their assigned frequency.

    Parameters
    ----------
    data : dict
        A dictionary where each key is the name of an SQL function and each value is a list of PVs for that function.
        Each PV is a dictionary with 'frequency', 'instrument', 'name', and 'function' keys.
        The units of 'frequency' are seconds, meaning the time interval between PV updates.
        The SQL functions are "pvUpdate" (updates a numeric PV) and "pvUpdateString" (updates a string PV).

    Yields
    ------
    tuple
        A tuple containing the SQL function name, instrument, name, and evaluated function value of the PV.
    """
    time_step = 0.5  # in seconds. Maximum frequency for any message to be sent
    count = 0
    while True:
        for sql_function, pvs in data.items():
            for pv in pvs:
                yield_tuple = (
                    sql_function,
                    pv["instrument"],
                    pv["name"],
                    eval(pv["function"].format(x=count * time_step)),
                )
                skip_counts = math.ceil(pv["frequency"] / time_step)
                if skip_counts == 0:  # only if frequency is 0
                    if count == 0:
                        yield yield_tuple
                elif count % skip_counts == 0:
                    yield yield_tuple
        time.sleep(time_step)
        count += 1


def broadcast(conn, pv_gen):
    """
    Sends process variable (PV) updates to the specified SQL functions in the database using an established connection.

    Parameters
    ----------
    conn : psycopg2.extensions.connection
        A connection object to the PostgreSQL database.
    pv_gen : generator
        A python generator that yields tuples containing the SQL function name, instrument, PV name, and PV value.
        The generator yields at specified intervals based on the frequency assigned to each PV.
    """
    cursor = conn.cursor()
    for function, inst, name, value in pv_gen:
        print(f"Sending {inst} {name} {value} to {function}")
        cursor.execute(f"SELECT * FROM {function}(%s, %s, %s, %s, %s)", [inst, name, value, 0, int(time.time())])
        conn.commit()


def connect_to_database(database, user, password, host, port):
    """
    Establishes a connection to a PostgreSQL database.

    Parameters
    ----------
    database : str
        The name of the database to connect to.
    user : str
        The username used to authenticate.
    password : str
        The password used to authenticate.
    host : str
        The host address of the database.
    port : str
        The port number on which the database is listening.

    Returns
    -------
    psycopg2.extensions.connection
        A connection object to the PostgreSQL database.
    """
    conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
    return conn


def get_options(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", dest="user", default=os.getenv("DATABASE_USER", "postgres"))
    parser.add_argument("--password", dest="password", default=os.getenv("DATABASE_PASS", "postgres"))
    parser.add_argument("--host", dest="host", default=os.getenv("DATABASE_HOST", "localhost"))
    parser.add_argument("--port", dest="port", default=os.getenv("DATABASE_PORT", "5432"))
    parser.add_argument("--database-name", dest="database", default=os.getenv("DATABASE_NAME", "workflow"))
    parser.add_argument(
        "--pv-files",
        "-f",
        dest="pv_files",
        default=service_content_files(),
        help="List of content files to broadcast, separated by commas",
    )
    options = parser.parse_args(argv)
    return options


def main(argv=None):
    options = get_options(argv)
    data = read_contents([f.strip() for f in options.pv_files.split(",")])
    connection = connect_to_database(options.database, options.user, options.password, options.host, options.port)
    broadcast(connection, pv_generator(data))


if __name__ == "__main__":
    main()
