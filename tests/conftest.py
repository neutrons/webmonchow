# standard imports
import os
import sys

# third-party imports
import pytest

this_module_path = sys.modules[__name__].__file__
repo_rootpath = os.path.dirname(os.path.dirname(this_module_path))


@pytest.fixture(scope="session")
def content_files():
    content = dict()
    amq_dirpath = os.path.join(repo_rootpath, "src", "webmonchow", "amq", "services")
    content["amq"] = {
        "dasmon": os.path.join(amq_dirpath, "dasmon.json"),
        "pvsd": os.path.join(amq_dirpath, "pvsd.json"),
        "translation": os.path.join(amq_dirpath, "translation.json"),
    }
    pv_dirpath = os.path.join(repo_rootpath, "src", "webmonchow", "pv", "services")
    content["pv"] = {"dasmon": os.path.join(pv_dirpath, "dasmon.json")}
    return content
