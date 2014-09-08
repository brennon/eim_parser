import os, re, sys, pymongo, logging, json, cProfile
from optparse import OptionParser
from subprocess import call
from pprint import pprint

def main():
    usage = "usage: %prog [base_directory]"
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--dir', dest='root_dir', default=None, help='root directory for parsing')
    (options, args) = parser.parse_args()

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

    if options.root_dir:
        root_dir = options.root_dir
    else:
        root_dir = os.getcwd()

    file_list = list()
    ignored_files = list()

    # Iterate over all files below root_dir
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if re.search('^T\d_S\d{4,}(?:_[HRST]\d{3})?.json$', f):
                filepath = os.path.abspath(os.path.join(root, f))
                logger.debug('Adding %s to worklist' % filepath)
                file_list.append(filepath)
            else:
                ignored_files.append(f)

    logger.info("Parsing %d .json files below %s" % (len(file_list), root_dir))
    logger.info("Ignoring %d files" % len(ignored_files))

    total_files = len(file_list)

    # Iterate over collected files
    for (count, f) in enumerate(file_list):
        collection = None
        if re.search('[HRST]\d{3}.json', f):
            collection = 'new_signals'
        else:
            collection = 'new_sessions'
            if not check_json_file(f):
                logger.info("Skipping file (%d/%d) %s" % (count + 1, total_files, f))
                continue

        logger.info("Importing file (%d/%d) %s" % (count + 1, total_files, f))
        call(['mongoimport', '-h', 'muse.cc.vt.edu', '-d', 'eim', '-c', collection, '-u', 'brennon', '-p', 'grimier320861!amputate', '--authenticationDatabase', 'admin', '--file', f])

def check_json_file(filepath):
    valid = True
    try:
        f = open(filepath, 'r')
        j = json.load(f)

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
