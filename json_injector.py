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
    fh = logging.FileHandler('json_injector')
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
            if re.search('^T\d_S\d{4,}(?:_[HRST]\d{3})?.json$', f):
                filepath = os.path.abspath(os.path.join(root, f))
                logger.debug('Adding %s to worklist' % filepath)
                file_list.append(filepath)
            else:
                ignored_files.append(f)

    logger.info("Parsing %d .json files below %s" % (len(file_list), root_dir))
    logger.info("Ignoring %d files" % len(ignored_files))

    # Iterate over collected files
    for f in file_list:
        collection = None
        if re.search('[HRST]\d{3}.json', f):
            collection = 'new_signals'
        else:
            collection = 'new_sessions'
        call(['mongoimport', '-h', 'muse.cc.vt.edu', '-d', 'eim', '-c', collection, '--file', f])

if __name__ == "__main__":
    main()
