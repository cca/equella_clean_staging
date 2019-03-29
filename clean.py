import datetime
import json
import os
import psycopg2
import shutil

# load configuration info
with open('config.json') as file:
    config = json.load(file)
    if config['debug'] is True:
        print('Debugging mode. No files nor database tuples will be affected.')


def connect():
    """ Connect to PostgreSQL database """
    print('Connecting to the PostgreSQL database...')
    return psycopg2.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        dbname=config['dbname'],
        port=config['port'],
    )

# from https://gist.github.com/hanleybrand/5224673
def hash128(str):
    """ return 7-bit hash of string """
    hash = 0
    for char in str:
        hash = (31 * hash + ord(char)) & 0xFFFFFFFF
        hash = ((hash + 0x80000000) & 0xFFFFFFFF) - 0x80000000
        # EQUELLA reduces hashes to values 0 - 127
        hash = hash & 127
    return hash


def get_path(uuid):
    """
    given staging area UUID, return it's path on the mounted filestore
    path is like /mnt/equelladata01/107/a61aa663-9829-4b9b-bb2c-512d48f46eaf
    NOTE: we actually have 2 filestores so we're just ignoring the secondary one
    for now, which only Industrial Design uses
    """
    return '/'.join([config['filestore'], str(hash128(uuid)), uuid])


def database_is_safe(stage, connection):
    """ check that staging.user_session value doesn't appear in other db tables """
    user_session = stage[1]
    # get a new db cursor
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM cached_value WHERE key = %s;', (user_session,))
    if cursor.fetchone() is not None:
        print('{} user session has a cache value in the database.').format(stage[0])
        cursor.close()
        return False

    cursor.execute('SELECT * FROM entity_lock WHERE user_session = %s;', (user_session,))
    if cursor.fetchone() is not None:
        print('{} user session has a locked entity in the database.').format(stage[0])
        cursor.close()
        return False

    # fallthrough - the stage's user session doesn't appear active
    print('{} is not associated with an active user session.').format(stage[0])
    cursor.close()
    return True


def files_are_old(uuid):
    """ check that the files in Staging are over a year old """
    staging_path = get_path(uuid)
    # directory might not exist so work around errors
    try:
        dir_listing = os.listdir(staging_path)
        if len(dir_listing) > 0:
            stat = os.stat(staging_path + '/' + dir_listing[0])
            now = datetime.datetime.now()
            # stat.st_mtime (last modified), stat.st_atime (last accessed),
            # & stat.st_ctime (last metadata change) are all options
            last_modified = datetime.datetime.fromtimestamp(stat.st_mtime)
            if (now - last_modified) < datetime.timedelta(days=365):
                print('{} files less than a year old.'.format(uuid))
                return False

        else:
            print('{} directory is empty.'.format(uuid))
            return True

    except OSError as err:
        print('Error accessing {0} files: {1}'.format(uuid, err))
        return True

    # fallthrough - there's a directory with files & they're old
    print('{} files are over a year old.'.format(uuid))
    return True


def main():
    """ main program logic """
    connection = connect()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM staging;')
    stage = cursor.fetchone()
    print('{} entries in staging database table to test.'.format(cursor.rowcount))

    while stage is not None:
        uuid = stage[0]
        print('Testing Staging area {} now.').format(uuid)
        if database_is_safe(stage, connection) and files_are_old(uuid):
            print('Staging {} looks safe to delete.').format(uuid)
            if config['debug'] is False:
                # delete files!! ignore errors bc sometimes path will be empty
                print('Deleting {}').format(get_path(uuid))
                shutil.rmtree(get_path(uuid), ignore_errors=True)
                # delete database row!!
                print('Database: DELETE FROM staging WHERE stagingid = {};').format(uuid)
                cursor2 = connection.cursor()
                cursor.execute('DELETE FROM staging WHERE stagingid = %s;', (uuid,))
                connection.commit()
                cursor2.close()

        stage = cursor.fetchone()

    # close db cursor and then connection
    cursor.close()
    connection.close()


if __name__ == '__main__':
    main()
