import re, datetime, sys, logging, os, json

experiment_locations = ['DUBLIN', 'NYC', 'BERGEN', 'SINGAPORE', 'MANILA']

def timestamp_to_millis(timestamp_string):
    """
    Converts a timestamp string of the format '02:14.667' to an integer
    representing the total number of milliseconds from 00:00.000

    >>> timestamp_to_millis('02:14.667')
    134667
    """
    match = re.search('(\d+):(\d{2}).(\d{3})', timestamp_string)
    minutes = int(match.groups()[0]) * 60000
    seconds = int(match.groups()[1]) * 1000
    return int(match.groups()[2]) + minutes + seconds

class EIMParsingError(Exception):
    pass

class EIMParser():

    def __init__(self, filepath, logger=None):
        """
        Initializes an EIMParser with a reference to the appropriate filepath.

        A filepath must be provided.
        >>> p = EIMParser(filepath = None)
        Traceback (most recent call last):
            ...
        ValueError: A filepath must be provided
        """
        if filepath == None: raise ValueError('A filepath must be provided')

        if logger == None:
            self.logger = logging.getLogger('eim_parser')
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger = logger

        self._filepath = os.path.abspath(filepath)
        self._file = None
        self._experiment_metadata = {'location':None, 'terminal':None, 'session_number':None}
        self.gather_metadata()
        self.version = None
        self.determine_file_version()

    def determine_file_version(self):
        """
        Determines the file version from among the four Dublin versions and the
        one version used everywhere else.

        >>> p = EIMParser('./test_data/DUBLIN/MuSE_SERVER/06-Jul-2010/T4_S0106_answers.txt')
        >>> p.determine_file_version()
        >>> p.version
        1

        >>> p = EIMParser('./test_data/DUBLIN/MuSE_SERVER/20-Aug-2010/T4_S0770_answers.txt')
        >>> p.determine_file_version()
        >>> p.version
        2

        >>> p = EIMParser('./test_data/DUBLIN/MuSE_SERVER/05-Sep-2010/T3_S1016_answers.txt')
        >>> p.determine_file_version()
        >>> p.version
        3

        >>> p = EIMParser('./test_data/DUBLIN/MuSE_SERVER/30-Sep-2010/T3_S1266_answers.txt')
        >>> p.determine_file_version()
        >>> p.version
        4

        >>> p = EIMParser('./test_data/NYC/SERVER_NYC/2011-07-07/terminals/T2/2011-07-07/T2_S0342_answers.txt')
        >>> p.determine_file_version()
        >>> p.version
        5
        """
        dublin_a = (datetime.datetime(2010,7,1),datetime.datetime(2010,7,21,23,59))
        dublin_b = (datetime.datetime(2010,7,23),datetime.datetime(2010,8,29,23,59))
        dublin_c = (datetime.datetime(2010,8,31),datetime.datetime(2010,9,19,23,59))
        dublin_d = (datetime.datetime(2010,9,21),datetime.datetime(2010,10,1,23,59))

        filetime = datetime.datetime.fromtimestamp(os.stat(self._filepath).st_mtime)

        if filetime >= dublin_a[0] and filetime <= dublin_a[1]:
            self.version = 1
            return
        elif filetime >= dublin_b[0] and filetime <= dublin_b[1]:
            self.version = 2
            return
        elif filetime >= dublin_c[0] and filetime <= dublin_c[1]:
            self.version = 3
            return
        elif filetime >= dublin_d[0] and filetime <= dublin_d[1]:
            self.version = 4
            return
        elif filetime >= dublin_d[1]:
            self.version = 5
            return

        raise EIMParsingError('Could not determine answer file version: %s' % self._filepath)

    def gather_metadata(self):
      """
      Gathers metadata for this document from the directory tree.

      >>> p = EIMParser('./test_data/SINGAPORE/SERVER/2012-07-20/SingaporeTerminal/T2/21-07-2012/experiment/T2_S0626_RESET.txt')
      >>> p._experiment_metadata['location'] = None
      >>> p._experiment_metadata['terminal'] = None
      >>> p.gather_metadata()
      >>> p._experiment_metadata['location']
      'singapore'
      >>> p._experiment_metadata['terminal']
      2
      """
      self.gather_location()
      self.gather_terminal()

    def gather_location(self):
      """
      Gathers experiment location for this document from the directory tree.

      >>> p = EIMParser('./test_data/SINGAPORE/SERVER/2012-07-20/SingaporeTerminal/T2/21-07-2012/experiment/T2_S0626_RESET.txt')
      >>> p._experiment_metadata['location'] = None
      >>> p.gather_location()
      >>> p._experiment_metadata['location']
      'singapore'
      """
      match = None
      for location in experiment_locations:
        match = re.search('(%s)' % location, self._filepath)
        if match:
          self._experiment_metadata['location'] = match.groups()[0].lower()
          return

      raise EIMParsingError('Could not determine location for %s' % self._filepath)

    def gather_terminal(self):
        """
        Gathers experiment terminal number for this document

        >>> p = EIMParser('./test_data/SINGAPORE/SERVER/2012-07-20/SingaporeTerminal/T2/21-07-2012/experiment/T2_S0626_RESET.txt')
        >>> p._experiment_metadata['terminal'] = None
        >>> p.gather_terminal()
        >>> p._experiment_metadata['terminal']
        2
        """
        match = None
        match = re.search('.*T(\d).*.txt', self._filepath)
        if match:
            self._experiment_metadata['terminal'] = int(match.groups()[0])
            return

        raise EIMParsingError('Could not determine terminal number for %s' % self._filepath)

    def open_file(self):
        """
        Opens the file at filepath and stores descriptor.

        >>> f = open('./.MANILA_T4_S9999_test.txt', 'a')
        >>> f.close()
        >>> parser = EIMParser(filepath = './.MANILA_T4_S9999_test.txt')
        >>> parser.open_file()
        True

        >>> parser._file.name == os.path.abspath('./.MANILA_T4_S9999_test.txt')
        True

        >>> parser._file.closed
        False

        >>> parser.close_file()
        >>> import os
        >>> os.unlink(f.name)
        """
        try:
            self._file = open(self._filepath, 'r')
            return True
        except:
            raise EIMParsingError('Could not open %s' % self._filepath)

    def close_file(self):
        """
        Closes the file at filepath.

        >>> f = open('./.MANILA_T4_S9898_test.txt', 'w')
        >>> f.close()
        >>> parser = EIMParser(filepath = './.MANILA_T4_S9898_test.txt')
        >>> parser.open_file()
        True
        >>> parser.close_file()
        >>> parser._file.closed
        True
        >>> import os
        >>> os.unlink(f.name)
        """
        if not self._file.closed: self._file.close()

    def parse(self):
        """
        Parses all lines in a file.

        >>> f = open('./.MANILA_T4_S9898_test.txt', 'w')
        >>> f.close()
        >>> parser = EIMParser(filepath = './.MANILA_T4_S9898_test.txt')
        >>> parser.parse()
        >>> parser._experiment_metadata['session_number']
        9898

        >>> import os
        >>> os.unlink(f.name)
        """
        try:
            self.open_file()
            lines = list(self._file)

            # If a date line is present, parse it first
            for number, line in enumerate(lines):
                if re.search('DATE', line):
                    try:
                        self.parse_line(line, number + 1)
                    except:
                        self.logger.error(e)
                    break

            # Parse all lines
            for number, line in enumerate(lines):
                try:
                    self.parse_line(line, number + 1)
                except Exception as e:
                    self.logger.error(e)

            # Parse session id
            match = re.search('T\d_S(\d{4})_.*.txt', self._filepath)
            if match:
                self._experiment_metadata['session_number'] = int(match.groups()[0])
            else:
                raise EIMParsingError("No valid session id found in filename %s" % self._filepath)

        except:
            raise

        finally:
            if self._file and not self._file.closed:
                self.close_file()

    def parse_line(self, line, number):
        pass

    def to_dict(self):
        base = dict()
        base['metadata'] = self._experiment_metadata
        return base

    def to_json_file(self):
        """
        Saves dict representation as a JSON file.

        >>> f = open('./.MANILA_T2_S9898_test.txt', 'w')
        >>> f.close()
        >>> p = EIMParser('./.MANILA_T2_S9898_test.txt')
        >>> p.to_json_file()
        >>> j = open('./.MANILA_T2_S9898_test.json', 'r')
        >>> import json
        >>> json_dict = json.load(j)
        >>> json_dict['metadata']['location']
        'manila'
        >>> json_dict['metadata']['session_number']

        >>> json_dict['metadata']['terminal']
        2
        >>> j.close()
        >>> os.unlink(f.name)
        >>> os.unlink(j.name)
        """
        current_dir = os.path.dirname(self._filepath)
        file_no_ext = os.path.splitext(os.path.basename(self._filepath))[0]
        try:
            f = open(os.path.join(current_dir, '%s.json' % file_no_ext), 'w')
            json.dump(self.to_dict(), f)
        except:
            raise EIMParsingError('Could not write JSON file for %s', self._filepath)
        finally:
            f.close()

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
