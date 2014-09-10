import os, re, sys, pymongo, logging, json, cProfile
from optparse import OptionParser
from pprint import pprint

def main():

    # Setup option parsing
    usage = "usage: %prog [base_directory]"
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--dir', dest='root_dir', default=None, help='root directory for parsing')
    (options, args) = parser.parse_args()

    # Configure file and STDOUT logging
    logger = logging.getLogger('json_compiler')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('json_compiler.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    # Use base directory if specified in options
    if options.root_dir:
        root_dir = options.root_dir

    # Otherwise, use the current working directory
    else:
        root_dir = os.getcwd()

    # Lists of files to parse/ignore
    file_list = list()
    ignored_files = list()

    # Iterate over all files below root_dir
    for root, dirs, files in os.walk(root_dir):
        for f in files:

            # If file has .json extension
            if re.search('.json$', f):

                # Add absolute path to file to file_list
                filepath = os.path.abspath(os.path.join(root, f))
                logger.debug('Adding %s to worklist' % filepath)
                file_list.append(filepath)

            # Otherwise, ignore it
            else:
                ignored_files.append(f)

    logger.info("Parsing %d .json files below %s" % (len(file_list), root_dir))
    logger.info("Ignoring %d files" % len(ignored_files))

    total_files = len(file_list)

    # Iterate over collected files
    for (count, f) in enumerate(file_list):

        # Get existing JSON dictionary
        prefix = None
        base_file = None
        signals_file = None
        base_filename = None
        signals_filename = None
        base_dict = dict()
        signals_dict = dict()
        success = True

        # Look for a 'prefix' in the filename, like 'T3_S0142'
        match = re.search('(.*T\d_S\d+)', f)
        if match:

            # Set the base filename to <prefix>.json
            prefix = match.groups()[0]
            base_filename = '%s.json' % prefix

            # signals_filename = '%s_signals.json' % prefix
        else:
            success = False

        # If we found a prefix and set the base filename
        if success:

            # Open the file and load existing JSON into base_dict
            try:
                base_file = open(base_filename, 'r')
                base_dict = json.load(base_file)

            # If that threw an exception, assign an empty dict to base_dict
            except:
                base_dict = dict()


            finally:
                if base_file and not base_file.closed:
                    base_file.close()

        if success:

            # Is this a reset file?
            if re.search('T\d_S\d{4,}_RESET.json', f):

                # Parse reset file
                print_skipping_status(count + 1, total_files, f, logger)

                # try:
                #     reset_file = open(f, 'r')
                #     reset_json = json.load(reset_file)
                #     base_dict.update(reset_json)
                #
                # except Exception as e:
                #     success = False
                #     logger.error("Error parsing %s: %s" % (f, e))
                #
                # finally:
                #     if not reset_file.closed:
                #         reset_file.close()

            # Is this an info file?
            elif re.search('T\d_S\d{4,}_1nfo.json', f):

                # Parse info file
                print_parsing_status(count + 1, total_files, f, logger)

                try:
                    # Open the file
                    info_file = open(f, 'r')

                    # Load the JSON into a dict
                    info_json = json.load(info_file)

                    # If metadata isn't complete in the base dictionary, get it from this file
                    if not metadata_is_complete(base_dict):
                        base_dict["metadata"] = info_json["metadata"]

                    # Put info file-specific data into the base_dict
                    base_dict["media"] = info_json["media"]
                    base_dict["date"] = info_json["date"]
                    base_dict["timestamps"] = info_json["timestamps"]

                except Exception as e:
                    success = False
                    logger.error("Error parsing %s: %s" % (f, e))

                finally:
                    if not info_file.closed:
                        info_file.close()

            # Is this a test file?
            elif re.search('T\d_S\d{4,}_TEST.json', f):

                # Parse test file
                print_skipping_status(count + 1, total_files, f, logger)

                # Build and use an EIMTestParser for this file
                # try:
                #     test_file = open(f, 'r')
                #     test_json = json.load(test_file)
                #     if 'signals' not in base_dict.keys():
                #         base_dict['signals'] = dict()
                #     base_dict['signals']['test'] = test_json['signals']['test']
                #
                # except Exception as e:
                #     success = False
                #     logger.error("Error parsing %s: %s" % (f, e))
                #
                # finally:
                #     if not test_file.closed:
                #         test_file.close()

            # Is this a song file?
            elif re.search('T\d_S\d{4,}_[HRST]\d{3,}.json', f):

                # Parse song file
                print_skipping_status(count + 1, total_files, f, logger)

                # Build and use an EIMSongParser for this file
                # try:
                #     song_file = open(f, 'r')
                #     song_json = json.load(song_file)
                #     if 'signals' not in base_dict.keys():
                #         base_dict['signals'] = dict()
                #
                #     match = re.search('T\d_S\d{4,}_([HRST]\d{3,})', f);
                #     this_song = match.groups()[0]
                #     base_dict['signals'][this_song] = song_json['signals']['songs'][this_song]
                #
                # except Exception as e:
                #     success = False
                #     logger.error("Error parsing %s: %s" % (f, e))
                #
                # finally:
                #     if not song_file.closed:
                #         song_file.close()

            # Is this an answer file?
            elif re.search('T\d_S\d{4,}_answers.json', f):

                # Parse answer file
                print_parsing_status(count + 1, total_files, f, logger)

                try:
                    # Open the file
                    answer_file = open(f, 'r')

                    # Load the JSON into a dict
                    answer_json = json.load(answer_file)

                    # If metadata isn't complete in the base dictionary, get it from this file
                    if not metadata_is_complete(base_dict):
                        base_dict["metadata"] = answer_json["metadata"]

                    # Put answer file-specific data into the base_dict
                    base_dict["answers"] = answer_json["answers"]

                except Exception as e:
                    success = False
                    logger.error("Error parsing %s: %s" % (f, e))

                finally:
                    if not answer_file.closed:
                        answer_file.close()


            # Is this a debug file?
            elif re.search('T\d_S\d{4,}_debug.json', f):

                # Parse debug file
                print_skipping_status(count + 1, total_files, f, logger)

                # try:
                #     debug_file = open(f, 'r')
                #     debug_json = json.load(debug_file)
                #     base_dict.update(debug_json)
                #
                # except Exception as e:
                #     success = False
                #     logger.error("Error parsing %s: %s" % (f, e))
                #
                # finally:
                #     if not debug_file.closed:
                #         debug_file.close()

        if success:
            base_file = open(base_filename, 'w')
            json.dump(base_dict, base_file)

        if base_file and not base_file.closed:
            base_file.close()

def print_parsing_status(current, total, filename, logger):
    logger.debug("(%d/%d) Parsing %s" % (current, total, filename))

def print_skipping_status(current, total, filename, logger):
    logger.debug("(%d/%d) Skipping %s" % (current, total, filename))

def metadata_is_complete(check_dict):
    if "metadata" not in check_dict:
        return False

    if "session_number" not in check_dict["metadata"]:
        return False
    elif not isinstance(check_dict["metadata"]["session_number"], int):
        return False

    if "terminal" not in check_dict["metadata"]:
        return False
    elif not isinstance(check_dict["metadata"]["terminal"], int):
        return False

    if "location" not in check_dict["metadata"]:
        return False
    elif not isinstance(check_dict["metadata"]["location"], str):
        return False

    return True

if __name__ == "__main__":
    main()
