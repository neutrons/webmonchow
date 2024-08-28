.. _developer:

Developer Documentation
=======================

.. contents::
   :local:
   :depth: 1

Local Environment
-----------------
For purposes of development, create conda environment `webmonchow` with file `environment.yml`, and then
install the package in development mode with `pip`:

.. code-block:: bash

   $> cd/path/to/webmonchow/
   $> conda create env --solver libmamba --file ./environment.yml
   $> conda activate webmonchow
   (webmonchow)$> pip install --no-deps -e ./

By installing the package in development mode, one doesn't need to re-install package `usanred` in conda
environment `webmonchow` after every change to the source code.
Option `--no-deps` ensures that `pip` does not install additional packages from `pyproject.toml`
into the development environment.

pre-commit Hooks
----------------

Activate the hooks by typing in the terminal:

.. code-block:: bash

   $> cd cd /path/to/mr_reduction/
   $> conda activate mr_reduction
   (mr_reduction)$> pre-commit install

Development procedure
---------------------

1. A developer is assigned with a task during neutron status meeting and changes the task's status to **In Progress**.
2. The developer creates a branch off *next* and completes the task in this branch.
3. The developer creates a pull request (PR) off *next*.
4. Any new features or bugfixes must be covered by new and/or refactored automated tests.
5. The developer asks for another developer as a reviewer to review the PR.
   A PR can only be approved and merged by the reviewer.
6. The developer changes the task’s status to **Complete** and closes the associated issue.

Running the tests
-----------------
Locally running the units tests:

.. code-block:: bash

   $> conda activate webmonchow
   (webmonchow)$> pytest -v  tests/

Listing the dependencies
------------------------
It is critical to list the dependencies both in the conda recipe `meta.yaml` and in the `pyproject.toml` file.
The first ensures a successful build of the conda package,
while the second enables us to install a feature branch of `webmonchow` in
`service webmonchow <https://github.com/neutrons/data_workflow/blob/next/Dockerfile.webmonchow>`_
of the `data_workflow` package.



Building the python wheel
-------------------------
Locally building the python wheel. At the root of the repo:

.. code-block:: bash

   $> conda activate webmonchow
   (webmonchow)$> python -m build  # generate the wheel
    (webmonchow)$> twine check dist/*  # check the wheel with twine

Building the conda package
--------------------------
Locally building the conda package. At the root of the repo:

.. code-block:: bash

   $> cd conda.recipe/
   $> conda activate webmonchow
   (webmonchow)$> conda mambabuild -c conda-forge --output-folder . .

If using `mamba` instead of `conda`, replace `conda mambabuild` with `mamba build`.


Building the documentation
--------------------------
A repository webhook is setup to automatically trigger the latest documentation build by GitHub actions.
To manually build the documentation:

.. code-block:: bash

   $> conda activate webmonchow
   (webmonchow)$> cd /path/to/webmonchow/docs
   (webmonchow)$> make docs

After this, point your browser to
`file:///path/to/webmonchow/docs/build/html/index.html`


Coverage reports
----------------

GitHuh actions create reports for unit and integration tests, then combine into one report and upload it to
`Codecov <https://app.codecov.io/gh/neutrons/webmonchow>`_.

Creating a stable release
-------------------------
- Follow the `Software Maturity Model <https://ornl-neutrons.atlassian.net/wiki/spaces/NDPD/pages/23363585/Software+Maturity+Model>`_
  for continuous versioning as well as creating release candidates and stable releases.
- Update the :ref:`Release Notes <release_notes>` with major fixes, updates and additions since last stable release.
