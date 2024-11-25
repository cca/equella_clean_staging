import os
import re
import shutil

import psycopg2

from clean import files_are_old, get_path
import config


UUID_REGEX = re.compile(
    r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}"
)


def connect():
    """Connect to PostgreSQL database"""
    print("Connecting to the PostgreSQL database...")
    return psycopg2.connect(
        host=config.host,
        user=config.user,
        password=config.password,
        dbname=config.dbname,
        port=config.port,
    )


def is_uuid(string):
    """retun True if string is a UUID"""
    if UUID_REGEX.match(string):
        return True
    return False


def make_stage_list(path):
    """walk staging dir and create a list of all directories"""
    stages = []
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            # only include directory names that are UUIDs
            if is_uuid(dir):
                stages.append(dir)

    return stages


def check_db(dirs, db):
    """test a list of staging directories for presence in the database_is_safe

    args:
        dirs: list of directories to test
        db: database connection

    no return value, issues printed to stdout
    """
    cursor = db.cursor()
    for stage in dirs:
        cursor.execute("SELECT * FROM staging WHERE stagingid = %s;", (stage,))
        result = cursor.fetchone()
        if result is None:
            print("ATTN: folder {} is not in staging database table.".format(stage))
            if not config.debug and files_are_old(stage):
                print("Deleting {}".format(get_path(stage)))
                shutil.rmtree(get_path(stage))
        else:
            print("{} is present in the database.".format(stage))

    cursor.close()


def main():
    """check that all staging directories are present in openEQUELLA database"""
    stages = make_stage_list(config.filestore)
    print("Testing {} directories...".format(len(stages)))
    db = connect()
    check_db(stages, db)
    db.close()


if __name__ == "__main__":
    main()
