import os, re, logging, json
from optparse import OptionParser
from subprocess import call

def main():

    # Configure OptionParser
    usage = "usage: %prog [base_directory]"
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--dir', dest='root_dir', default=None, help='root directory for parsing')
    (options, args) = parser.parse_args()

    # Configure logging to STDOUT and file
    logger = logging.getLogger('json_injector')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('json_injector.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    # Use base directory if passed as option
    if options.root_dir:
        root_dir = options.root_dir

    # Otherwise, work in the current directory
    else:
        root_dir = os.getcwd()

    file_list = list()
    ignored_files = list()

    # Iterate over all files below root_dir
    for root, dirs, files in os.walk(root_dir):
        for f in files:

            # If a filename matches something like T2_S0134.json or T2_S0134_H001.json,
            # add it to the worklist
            if re.search('^T\d_S\d{4,}(?:_[HRST]\d{3})?.json$', f):
                filepath = os.path.abspath(os.path.join(root, f))
                logger.debug('Adding %s to worklist' % filepath)
                file_list.append(filepath)

            # Otherwise, add it to the list of ignored files
            else:
                ignored_files.append(f)

    logger.info("Parsing %d .json files below %s" % (len(file_list), root_dir))
    logger.info("Ignoring %d files" % len(ignored_files))

    total_files = len(file_list)

    # Iterate over collected files
    for (count, f) in enumerate(file_list):

        # MongoDB collection to which we will write
        collection = None

        # If this is a file like T2_S0134_H001.json, as opposed to one like T2_S0134.json,
        # send it to the new_signals collection
        if re.search('[HRST]\d{3}.json', f):
            collection = 'new_signals'

        # Otherwise, send it to the new_sessions collection
        # TODO: Change to new_trials collection
        else:
            collection = 'new_sessions'

            # If this file doesn't pass muster, skip it
            if not check_json_file(f):
                logger.info("Skipping file (%d/%d) %s" % (count + 1, total_files, f))
                continue

        # Call `mongoimport` to send the file to the MongoDB server
        logger.info("Importing file (%d/%d) %s" % (count + 1, total_files, f))
        call(['mongoimport', '-h', 'muse.cc.vt.edu', '-d', 'eim', '-c', collection, '-u', 'Credentials.databaseUsername', '-p', 'Credentials.databasePassword', '--authenticationDatabase', 'admin', '--file', f])

# Check validity of JSON file
def check_json_file(filepath):
    valid = True
    try:
        # Make sure it exists and contains valid JSON
        f = open(filepath, 'r')
        j = json.load(f)

        # Make sure dict from JSON contains answers, metadata, media, and timestamps properties
        if not 'answers' in j:
            valid = False
        if not 'metadata' in j:
            valid = False
        if not 'media' in j:
            valid = False
        if not 'timestamps' in j:
            valid = False
    except:
        valid = False
    finally:
        if f and not f.closed:
            f.close()

    return valid

if __name__ == "__main__":
    main()
