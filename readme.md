# Clean up EQUELLA Staging Folder

There's some 1.3TB of files left in /mnt/equelladata01/Staging many of which are years old and should have been deleted a long time ago.

**Algorithm**:

1. from list of `staging` database tuples
1. check that `staging.user_session` is not in `cached_value.key`
1. check that `staging.user_session` is not in `entity_lock.user_session`
1. check that `staging.user_session` is not in `item_lock.user_session`
1. enter {{7-bit hash of staging.stagingid}}/{{staging.stagingid}} directory
1. check last modified date (_of every file? of just one random file?_)
1. if last modified over a year ago plus the checks above passed, then
    + delete the directory and its contents
    + remove the row from the `staging` database table

## Setup

Made for Python 2.7 as that's what we have on our Ubuntu servers. Also I'm using psychopg2-binary so we don't need to install postgres build tools (`pg_config` etc.) on the server.

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

Script won't delete files with debug mode on. Outputs a lot of text about each entry in the "staging" database table. There are no command line flags, just run `python clean.py`. You will likely need to start a `root` user shell session to run the script within, otherwise you might not have permission to access the mounted filestore.

Won't work on Windows because a "/" path separator is hard-coded but it would be easy to change that. Also not made to work with multiple openEQUELLA filestores.

# LICENSE

[ECL Version 2.0](https://opensource.org/licenses/ECL-2.0)
