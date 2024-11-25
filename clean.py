import datetime
import os
import shutil

import psycopg2
from sortedcontainers import SortedList

import config

# if we have a list of duplicate files, load it into a sorted list
if config.duplicates_file:
    dupes = []
    with open(config.duplicates_file, "r") as file:
        for line in file:
            dupes.append(line)

    sorted_dupes = SortedList(dupes)


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


# from https://gist.github.com/hanleybrand/5224673
def hash128(str):
    """return 7-bit hash of string"""
    hash = 0
    for char in str:
        hash = (31 * hash + ord(char)) & 0xFFFFFFFF
        hash = ((hash + 0x80000000) & 0xFFFFFFFF) - 0x80000000
        # EQUELLA reduces hashes to values 0 - 127
        hash = hash & 127
    return hash


def get_path(uuid):
    """
    given staging area UUID, return its path on the mounted filestore
    path is like /mnt/equelladata01/107/a61aa663-9829-4b9b-bb2c-512d48f46eaf
    NOTE: we actually have 2 filestores so we're just ignoring the secondary one
    for now, which only Industrial Design uses
    """
    return os.path.join(config.filestore, str(hash128(uuid)), uuid)


def database_is_safe(stage, db):
    """check that staging.user_session value doesn't appear in other db tables"""
    user_session = stage[1]
    # get a new db cursor
    cursor = db.cursor()

    cursor.execute("SELECT * FROM cached_value WHERE key = %s;", (user_session,))
    if cursor.fetchone() is not None:
        print(f"{stage[0]} user session has a cache value in the database.")
        cursor.close()
        return False

    cursor.execute(
        "SELECT * FROM entity_lock WHERE user_session = %s;", (user_session,)
    )
    if cursor.fetchone() is not None:
        print(f"{stage[0]} user session has a locked entity in the database.")
        cursor.close()
        return False

    cursor.execute("SELECT * FROM item_lock WHERE user_session = %s;", (user_session,))
    if cursor.fetchone() is not None:
        print(f"{stage[0]} user session has a locked item in the database.")
        cursor.close()
        return False

    # fallthrough - the stage's user session doesn't appear active
    print(f"{stage[0]} is not associated with an active user session.")
    cursor.close()
    return True


def files_are_old(uuid):
    """check that the files in Staging are over a year old"""
    staging_path = get_path(uuid)
    # directory might not exist so work around errors
    try:
        dir_listing = os.listdir(staging_path)
        if len(dir_listing) > 0:
            stat = os.stat(os.path.join(staging_path, dir_listing[0]))
            now = datetime.datetime.now()
            # stat.st_mtime (last modified), stat.st_atime (last accessed),
            # & stat.st_ctime (last metadata change) are all options
            last_modified = datetime.datetime.fromtimestamp(stat.st_mtime)
            if (now - last_modified) < datetime.timedelta(days=365):
                print("{} files less than a year old.".format(uuid))
                return False

        else:
            print("{} directory is empty.".format(uuid))
            return True

    except OSError as err:
        print("Error accessing {0} files: {1}".format(uuid, err))
        return True

    # fallthrough - there's a directory with files & they're old
    print("{} files are over a year old.".format(uuid))
    return True


def files_are_dupes(uuid):
    """check that all files are in our list of duplicates"""
    staging_path = get_path(uuid)

    if os.path.exists(staging_path):
        # for each step on the walk, root is the dir we're in, dirs is a tuple
        # of all sub-directories, and files is a tuple of file names in the dir
        for root, dirs, files in os.walk(staging_path):
            for file in files:
                filepath = os.path.join(root, file)
                if filepath not in sorted_dupes:
                    print(f"{filepath} is not in the duplicates list")
                    return False

        print(f"{uuid} files are duplicated somewhere in storage.")
        return True

    else:
        print(f"{staging_path} does not exist.")
        return True


def files_ok(uuid):
    """combine the two file system checks (age, duplicity) into one"""
    # since these checks are slow, nest them so we don't need to run the second
    # if the first one fails
    if files_are_old(uuid):
        # only run second test if we have a dupes list
        if config.duplicates_file:
            return files_are_dupes(uuid)
        return True
    return False


def main():
    db = connect()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM staging;")
    print(f"{cursor.rowcount} entries in staging database table to test.")

    for stage in cursor:
        uuid = stage[0]
        print(f"{datetime.datetime.now()} - testing Staging area {uuid}")
        if database_is_safe(stage, db) and files_ok(uuid):
            print(f"Staging {uuid} looks safe to delete.")
            if config.debug is False:
                # delete files!! ignore errors bc sometimes path will be empty
                print(f"Deleting {get_path(uuid)}")
                shutil.rmtree(get_path(uuid), ignore_errors=True)
                # delete database row!!
                print(f"Database: DELETE FROM staging WHERE stagingid = {uuid};")
                cursor2 = db.cursor()
                cursor2.execute(f"DELETE FROM staging WHERE stagingid = {uuid};")

    # close db cursor and then db connection
    db.commit()
    cursor.close()
    db.close()


if __name__ == "__main__":
    if config.debug:
        print("Debugging mode. No files nor database tuples will be affected.")
    main()
