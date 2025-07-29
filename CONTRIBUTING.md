# Tests

## Run all the tests
```bash
tox
```

## Run specific python version

```bash
tox -e python3.12-extra-deps
```

## Filtering tests further

```bash
tox -e ... -- path/to/test/file.py -k <substring_of_test_name>
```

or to speedup the process, look into `tox.ini` and run commands without tox environment:

```bash
pip install -r test_requirements.txt -r test_requirements_extra.txt

# to run one and only one test
pytest path/to/test/file.py -k <substring_of_test_name>

# to run only flakes
pytest --flakes src/ examples/
```

Bash above is just examples how to run some of the commands without tox, there many more possibilities.

## Test cassetes

In some tests we are using [pytest-recording](https://github.com/kiwicom/pytest-recording) library to record
http requests to a local test cassetes to not to use network in future runs and to increase determinacy
of test runs (with the assupmtion that backend will not break contract and will not make any breaking changes).

But pytest-recording supports only http/https cassetes so we have something like this for grpc requests
[written by us](src/yandex_cloud_ml_sdk/_testing/interceptor.py).

It is not so convenient to use and have it's problems, but basically to use it you need to:

1) Place `@pytest.mark.allow_grpc` to the test.

2) Edit `tests/conftest.py:fixture_folder_id` (TODO: make it using env vars by default)

3) Export any auth into environment like `export YC_API_KEY="..."` or any other auth method

4) Run your new test for the first time `pytest path/to/test/file.py -k <test_name> --generate-grpc` which will create
  a new cassete file

5) In case of the test failed or if you want to regenerate cassete -- `pytest <...> --regenerate-grpc` will help

6) When you will thinkn that cassete is okay, run pytest without any `--...-grpc` flags

7) Do not forget to commit new cassete file.


# Pre-commit hooks

We are using https://pre-commit.com/ to improve our PR review experience.

It is generally a good idea to setup pre-commit locally, otherwise some robot will come to your PR and
will either make commit with fixes (and you will need to pull it or overwrite with a force push),
either it will break the tests with the things it can't fix.


# Documentation

On PR we are running `sphinx-build -W` which are failing in case of any warnings such as
unresolved references or wrong rst syntaxt in docstrings.

To install sphinx and other required for work with documentation, run
`pip isntall -r docs/requirements.txt -e .` in the repo root.

To run sphinx locally to check if there are any errors or warnings,
run `sphinx-build docs docs/_build -E -W` in the repo root.
It will generate html in the `docs/_build` folder which you could check out in case
you want to be sure how is your doc will looks like.

Also you could install `sphinx-autobuild` and run `sphinx-autobuild docs docs/_build --watch src`
to run a webserver (it will be available at http://localhost:8000 by-default) and automatically
rebuild a doc when you save a file.
