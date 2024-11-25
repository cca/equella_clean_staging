# Clean up EQUELLA Staging Folder

There's some 1.3TB of files left in /mnt/equelladata01/Staging many of which are years old and should have been deleted a long time ago.

**Algorithm**:

1. from list of `staging` database tuples
1. check that `staging.user_session` is not in `cached_value.key`
1. check that `staging.user_session` is not in `entity_lock.user_session`
1. check that `staging.user_session` is not in `item_lock.user_session`
1. enter {{7-bit hash of staging.stagingid}}/{{staging.stagingid}} directory
1. check that the last modified date is over a year ago
    + _NOTE_: just does this for the first file/dir in `os.listdir` which should be fine
1. check that all files are in a list of duplicates (if we have such a list)
1. if all the checks above passed, then
    + delete the directory and its contents
    + remove the row from the `staging` database table

That's clean.py, which looks at the EQUELLA database then to the files. The dircheck.py script goes in the other direction and looks at UUID-named directories under the Staging path, trying to find references to them in the database. Neither will delete files or database rows if `config.debug` is `True`.

## Setup

We _should_ be able to set this up and run it using python 3 on our servers, but it was originally written for 2.7. Python on the server is 3.4.3. We can't use f-strings and the psycopg2 version is chosen to work with this older python. We may need to `apt-get install libpq-dev` to get it to work.

```sh
> pip install -r requirements.txt
> cp example.config.py config.py
> vim config.py
```

**config.py**:

```python
host = "db.example.com"
user = "username"
password = "sup3rsecr3t"
dbname = "equella"
port = 5432
filestore = "/path/to/Staging"
duplicates_file = "dupes.txt"
debug = True
```

The "duplicates_file" is an optional list of files known to be duplicated somewhere else in storage. This lets us check that it's 100% safe to remove a file before doing so. It is an optional parameter; if not provided, the script simply skips over this check. I've used [fdupes](https://github.com/adrianlopezroche/fdupes) to generate this text file.

The script will not delete files in `debug` mode. Outputs a lot of text about each entry in the "staging" database table. There are no command line flags, just run `python3 clean.py` or `python3 dircheck.py`. The script needs to run as root, otherwise it cannot access the mounted filestore. I recommend making config.py readable only by root (`chmod 400 config.py`).

## LICENSE

[ECL Version 2.0](https://opensource.org/licenses/ECL-2.0)
