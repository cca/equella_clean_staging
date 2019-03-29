# Clean up EQUELLA Staging Folder

There's some 1.3TB of files left in /mnt/equelladata01/Staging many of which are years old and should have been deleted a long time ago.

**Algorithm**:

1. from list of staging.stagingid UUIDs
1. check if related staging.user_session is in cached_value.key
1. check if staging.user_session is in entity_lock.user_session
1. enter {hash}/{uuid} directory
1. check last modified date (_of every file? of just one random file?_)
1. if last modified over a year ago plus 2) & 3) above passed, then
    + delete the directory and its contents
    + remove the row from the staging database table

## Setup

Made for Python 2.7 as that's what we have on our Ubuntu servers. Also I'm using psychopg2-binary so we don't need the postgres build tools (`pg_config` etc.) installed on the server.

```sh
> virtualenv .
> source bin/activate
> pip install -r requirements.txt
> vim config.json
```

**config.json**:

```json
{
    "host": "db.example.com",
    "user": "username",
    "password": "sup3rsecr3t",
    "dbname": "equella",
    "port": 5432,
    "filestore": "/path/to/Staging",
    "debug": true
}
```

Script won't delete files with debug mode on. Outputs a lot of text about each entry in the "staging" database table. There are no command line flags, just run `python clean.py`.

Won't work on Windows because a "/" path separator is hard-coded but it would be easy to change that. Also not made to work with multiple openEQUELLA filestores.
