import os
import re

import psycopg2

import config


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
    if re.match(
        r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
        string,
    ):
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
        cursor.execute(f"SELECT * FROM staging WHERE stagingid = {stage};")
        result = cursor.fetchone()
        if result is None:
            print(f"ATTN: folder {stage} is not in staging database table.")
        else:
            print(f"{stage} is present in the database.")

    cursor.close()


def main():
    """check that all staging directories are present in openEQUELLA database"""
    stages = make_stage_list(config.filestore)
    print(f"Testing {len(stages)} directories...")
    db = connect()
    check_db(stages, db)
    db.close()


if __name__ == "__main__":
    main()
