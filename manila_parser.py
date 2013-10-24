from optparse import OptionParser
import os, re, sys, pymongo
from eim_parser import EIMParser, EIMParsingError
from eim_info_parser import EIMInfoParser
from eim_test_parser import EIMTestParser, EIMSongParser
from eim_answers_parser import EIMAnswersParser
from eim_debug_parser import EIMDebugParser
from eim_db_connector import EIMDBConnector
from pprint import pprint
import logging
import cProfile

def main():
    usage = "usage: %prog [base_directory]"
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--dir', dest='root_dir', default=None, help='root directory for parsing')
    (options, args) = parser.parse_args()

    logger = logging.getLogger('manila_parser')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('manila_parser.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    if options.root_dir:
        root_dir = options.root_dir
    else:
        root_dir = os.getcwd()

    file_list = list()
    ignored_files = list()

    # Iterate over all files below root_dir
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if re.search('.txt$', f):
                filepath = "%s/%s" % (root, f)
                logger.info('Adding %s to worklist' % filepath)
                file_list.append(filepath)
            else:
                ignored_files.append(f)

    logger.info("Parsing %d .txt files below %s" % (len(file_list), root_dir))
    logger.info("Ignoring %d files" % len(ignored_files))

    # Determine data file types from among:
    # reset, test, info, answers, debug, and song
    type_counts = {
        'RESET':0,
        'INFO':0,
        'TEST':0,
        'ANSWERS':0,
        'DEBUG':0,
        'SONG':0,
        'UNKNOWN':0}


    # Create database connector
    db = EIMDBConnector(logger)

    try:
        db.connect()
        db.authenticate_to_database('eim', 'eim', 'emotoheaven')
    except:
        logger.critical('Could not connect and authenticate to database--exiting.')
        sys.exit()

    # Iterate over collected files
    for f in file_list:
        # Is this a reset file?
        if re.search('T\d_S\d{4,}_RESET.txt', f):
            # Parse reset file
            type_counts['RESET'] += 1

        # Is this an info file?
        if re.search('T\d_S\d{4,}_1nfo.txt', f):
            # Parse info file
            logger.info("Parsing %s" % f)

            # Build and use an EIMInfoParser for this file
            try:
                p = EIMInfoParser(f, logger)
                p.parse()
                p.to_json_file()

            except Exception as e:
                logger.error("Error parsing %s: %s" % (f, e))

            # Update counts
            type_counts['INFO'] += 1

        # Is this a test file?
        elif re.search('T\d_S\d{4,}_TEST.txt', f):
            # Parse test file
            logger.info("Parsing %s" % f)

            # Build and use an EIMTestParser for this file
            try:
                p = EIMTestParser(f, logger)
                p.parse()
                p.to_json_file()

            except:
                logger.error("Error parsing %s" % f)

            # Update counts
            type_counts['TEST'] += 1

        # Is this a song file?
        elif re.search('T\d_S\d{4,}_[HRST]\d{3,}.txt', f):
            # Parse song file
            logger.info("Parsing %s" % f)

            # Build and use an EIMSongParser for this file
            try:
                p = EIMSongParser(f, logger)
                p.parse()
                p.to_json_file()

            except:
                logger.error("Error parsing %s" % f)

            # Update counts
            type_counts['SONG'] += 1

        # Is this an answer file?
        elif re.search('T\d_S\d{4,}_answers.txt', f):

            # Parse answer file
            logger.info("Parsing %s" % f)

            # Build and use an EIMAnswersParser for this file
            try:
                p = EIMAnswersParser(f, logger)
                p.parse()
                p.to_json_file()

            except:
                logger.error("Error parsing %s" % f)

            # Update counts
            type_counts['ANSWERS'] += 1

        # Is this a debug file?
        elif re.search('T\d_S\d{4,}_debug.txt', f):

            # Parse debug file
            logger.info("Parsing %s" % f)

            # Build and use an EIMDebugParser for this file
            try:
                p = EIMDebugParser(f, logger)
                p.parse()
                p.to_json_file()

            except:
                logger.error("Error parsing %s" % f)

            # Update counts
            type_counts['DEBUG'] += 1

        else:
            type_counts['UNKNOWN'] += 1
            print("WARNING - Unrecognized file:",f)

    logger.info(type_counts)

if __name__ == "__main__":
    cProfile.run('main()', 'manila_parser.prof')
