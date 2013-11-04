import os, re, sys, pymongo, logging, json, cProfile
from optparse import OptionParser
from eim_parser import EIMParser, EIMParsingError
from eim_info_parser import EIMInfoParser
from eim_test_parser import EIMTestParser, EIMSongParser
from eim_answers_parser import EIMAnswersParser
from eim_debug_parser import EIMDebugParser
from eim_db_connector import EIMDBConnector
from pprint import pprint

def main():
    usage = "usage: %prog [base_directory]"
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--dir', dest='root_dir', default=None, help='root directory for parsing')
    (options, args) = parser.parse_args()

    logger = logging.getLogger('json_loader')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('json_loader')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
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
            if re.search('.json$', f):
                filepath = os.path.abspath(os.path.join(root, f))
                logger.debug('Adding %s to worklist' % filepath)
                file_list.append(filepath)
            else:
                ignored_files.append(f)

    logger.info("Parsing %d .json files below %s" % (len(file_list), root_dir))
    logger.info("Ignoring %d files" % len(ignored_files))

    # Iterate over collected files
    for f in file_list:

        # Get existing JSON dictionary
        prefix = None
        base_file = None
        base_filename = None
        base_dict = dict()
        success = True

        match = re.search('(.*T\d_S\d+)', f)
        if match:
            prefix = match.groups()[0]
            base_filename = '%s.json' % prefix
        else:
            success = False

        if success:

            base_file = open(base_filename, 'r')
            try:
                base_dict = json.load(base_file)
            except:
                pass
            finally:
                if base_file and not base_file.closed:
                    base_file.close()

        if success:

            # Is this a reset file?
            if re.search('T\d_S\d{4,}_RESET.json', f):

                # Parse reset file
                logger.debug("Parsing %s" % f)

                try:
                    reset_file = open(f, 'r')
                    reset_json = json.load(reset_file)
                    base_dict.update(reset_json)

                except Exception as e:
                    success = False
                    logger.error("Error parsing %s: %s" % (f, e))

                finally:
                    if not reset_file.closed:
                        reset_file.close()

            # Is this an info file?
            elif re.search('T\d_S\d{4,}_1nfo.json', f):

                # Parse info file
                logger.debug("Parsing %s" % f)

                try:
                    info_file = open(f, 'r')
                    info_json = json.load(info_file)
                    base_dict.update(info_json)

                except Exception as e:
                    success = False
                    logger.error("Error parsing %s: %s" % (f, e))

                finally:
                    if not info_file.closed:
                        info_file.close()

            # Is this a test file?
            elif re.search('T\d_S\d{4,}_TEST.json', f):

                # Parse test file
                logger.debug("Parsing %s" % f)

                # Build and use an EIMTestParser for this file
                try:
                    test_file = open(f, 'r')
                    test_json = json.load(test_file)
                    if 'signals' not in base_dict.keys():
                        base_dict['signals'] = dict()
                    base_dict['signals']['test'] = test_json['signals']['test']

                except Exception as e:
                    success = False
                    logger.error("Error parsing %s: %s" % (f, e))

                finally:
                    if not test_file.closed:
                        test_file.close()

            # Is this a song file?
            elif re.search('T\d_S\d{4,}_[HRST]\d{3,}.json', f):

                # Parse song file
                logger.debug("Parsing %s" % f)

                # Build and use an EIMSongParser for this file
                try:
                    song_file = open(f, 'r')
                    song_json = json.load(song_file)
                    if 'signals' not in base_dict.keys():
                        base_dict['signals'] = dict()

                    match = re.search('T\d_S\d{4,}_([HRST]\d{3,})', f);
                    this_song = match.groups()[0]
                    base_dict['signals'][this_song] = song_json['signals']['songs'][this_song]

                except Exception as e:
                    success = False
                    logger.error("Error parsing %s: %s" % (f, e))

                finally:
                    if not song_file.closed:
                        song_file.close()

            # Is this an answer file?
            elif re.search('T\d_S\d{4,}_answers.json', f):

                # Parse answer file
                logger.debug("Parsing %s" % f)

                try:
                    answer_file = open(f, 'r')
                    answer_json = json.load(answer_file)
                    base_dict.update(answer_json)

                except Exception as e:
                    success = False
                    logger.error("Error parsing %s: %s" % (f, e))

                finally:
                    if not answer_file.closed:
                        answer_file.close()


            # Is this a debug file?
            elif re.search('T\d_S\d{4,}_debug.json', f):

                # Parse debug file
                logger.debug("Parsing %s" % f)

                try:
                    debug_file = open(f, 'r')
                    debug_json = json.load(debug_file)
                    base_dict.update(debug_json)

                except Exception as e:
                    success = False
                    logger.error("Error parsing %s: %s" % (f, e))

                finally:
                    if not debug_file.closed:
                        debug_file.close()

        if success:
            base_file = open(base_filename, 'w')
            json.dump(base_dict, base_file)

        if base_file and not base_file.closed:
            base_file.close()

if __name__ == "__main__":
    main()
