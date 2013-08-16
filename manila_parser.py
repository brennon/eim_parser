from optparse import OptionParser
import os
import re
import pymongo
from eim_parser import EIMInfoParser
from eim_db_connector import EIMDBConnector
from pprint import pprint

def main():
    usage = "usage: %prog [base_directory]"
    parser = OptionParser(usage=usage)

    root_dir = os.getcwd()

    file_list = list()
    ignored_files = list()

    # Iterate over all files below root_dir
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if re.search('.txt$', f):
                filepath = "%s/%s" % (root, f)
                print(filepath)
                file_list.append(filepath)
            else:
                ignored_files.append(f)

    print("Parsing %d .txt files below %s" % (len(file_list), root_dir))
    print("Ignoring %d files" % len(ignored_files))

    # Determine data file types from among:
    # reset, test, info, answers, debug, and song
    type_counts = {
            'RESET':0,
            'INFO':0,
            'TEST':0,
            'ANSWERS':0,
            'DEBUG':0,
            'SONG':0,
            'UNKNOWN':0
            }

    # Create database connector
    db = EIMDBConnector()
    db.connect()
    db.authenticate_to_database('eim', 'eim', 'emotoheaven')

    # Iterate over collected files
    for f in file_list:
        """
        # Is this a reset file?
        if re.search('T\d_S\d{4,}_RESET.txt', f):
            # Parse reset file
            type_counts['RESET'] += 1
        """

        # Is this an info file?
        if re.search('T\d_S\d{4,}_1nfo.txt', f):
            # Parse info file
            print("Parsing %s" % f)

            # Build and use an EIMInfoParser for this file
            p = EIMInfoParser(f)
            p.parse()
            info_dict = p.to_dict()
            pprint(info_dict)

            # Insert in database using EIMDBConnector
            try:
                db.upsert_by_session_id(info_dict['session_id'], info_dict)
                print("\tSuccess!")
            except:
                print("\tFailed")

            # Update counts
            type_counts['INFO'] += 1

        """
        # Is this a test file?
        elif re.search('T\d_S\d{4,}_TEST.txt', f):
            # Parse test file
            type_counts['TEST'] += 1

        # Is this an answer file?
        elif re.search('T\d_S\d{4,}_answers.txt', f):
            # Parse answer file
            type_counts['ANSWERS'] += 1

        # Is this a debug file?
        elif re.search('T\d_S\d{4,}_debug.txt', f):
            # Parse debug file
            type_counts['DEBUG'] += 1

        # Is this a song file?
        elif re.search('T\d_S\d{4,}_[HRST]\d{3,}.txt', f):
            # Parse song file
            type_counts['SONG'] += 1

        else:
            type_counts['UNKNOWN'] += 1
            print("WARNING - Unrecognized file:",f)

        """

    print(type_counts)

if __name__ == "__main__":
    main()
