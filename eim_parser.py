import re, datetime, sys, logging, os

experiment_locations = ['DUBLIN', 'NYC', 'BERGEN', 'SINGAPORE', 'MANILA']

def timestamp_to_millis(timestamp_string):
    """
    Converts a timestamp string of the format '02:14.667' to an integer representing
    the total number of milliseconds from 00:00.000

    >>> timestamp_to_millis('02:14.667')
    134667
    """
    match = re.search('(\d+):(\d{2}).(\d{3})', timestamp_string)
    minutes = int(match.groups()[0]) * 60000
    seconds = int(match.groups()[1]) * 1000
    return int(match.groups()[2]) + minutes + seconds

class EIMParsingError(Exception):
    pass

class EIMParserLogger():
    logger_levels = ['INFO', 'WARN', 'ERROR', 'FAILURE']

    def __init__(self, level='WARN'):
        """
        New EIMParserLogger

        >>> l = EIMParserLogger()
        >>> l.level
        'WARN'
        >>> l = EIMParserLogger('INFO')
        >>> l.level
        'INFO'
        """
        if level in EIMParserLogger.logger_levels:
            self.level = level

    def log(self, message, level):
        """
        Logs a message to the console.

        >>> l = EIMParserLogger('INFO')
        >>> l.log('Some information', 'INFO')
        [INFO]: Some information
        >>> l = EIMParserLogger('WARN')
        >>> l.log('Some information', 'INFO')
        >>> l.log('A warning', 'WARN')
        [WARN]: A warning
        """
        if EIMParserLogger.logger_levels.index(level) >= EIMParserLogger.logger_levels.index(self.level):
            print('[%s]: %s' % (level.upper(), message))

class EIMParser():

    def __init__(self, filepath, logger=None):
        """
        Initializes an EIMParser with a reference to the appropriate filepath.

        A filepath must be provided:
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
        self._experiment_metadata = {'location':None, 'terminal':None, 'session_id':None}
        self.gather_metadata()

    def gather_metadata(self):
      """
      Gathers metadata for this document from the directory tree.

      >>> p = EIMParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt')
      """
      self.gather_location()
      self.gather_terminal()

    def gather_location(self):
      """
      Gathers experiment location for this document from the directory tree.

      >>> p = EIMParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt')
      >>> p._experiment_metadata['location']
      'Manila'
      """
      match = None
      for location in experiment_locations:
        match = re.search('(%s)' % location, self._filepath)
        if match:
          self._experiment_metadata['location'] = match.groups()[0].lower().capitalize()
          return

      raise EIMParsingError('Could not determine location for %s' % self._filepath)

    def gather_terminal(self):
        match = None
        match = re.search('T(\d)_\w\d+_.*.txt', self._filepath)
        if match:
            self._experiment_metadata['terminal'] = int(match.groups()[0])
            return

        raise EIMParsingError('Could not determine terminal number for %s' % self._filepath)

    def open_file(self):
        """
        Opens the file at filepath and stores descriptor.

        >>> f = open('./.T4_S9999_test.txt', 'a')
        >>> f.close()
        >>> parser = EIMParser(filepath = './.T4_S9999_test.txt')
        >>> parser.open_file()
        True

        >>> parser._file.name == os.path.abspath('./.T4_S9999_test.txt')
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

        >>> f = open('./T4_S9898_test.txt', 'w')
        >>> f.close()
        >>> parser = EIMParser(filepath = './T4_S9898_test.txt')
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
                self._experiment_metadata['session_id'] = int(match.groups()[0])
            else:
                raise EIMParsingError("No valid session id found in filename %s" % self._filepath)

        except:
            raise

        finally:
            if self._file and not self._file.closed:
                self.close_file()

    def parse_line(self, line, number):
        pass

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
