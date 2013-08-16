import re
import datetime

class EIMParser():

    def __init__(self, filepath):
        """
        Initializes an EIMParser with a reference to the appropriate filepath.

        A filepath must be provided:
        >>> p = EIMParser(filepath = None)
        Traceback (most recent call last):
            ...
        ValueError: A filepath must be provided
        """
        if filepath == None: raise ValueError('A filepath must be provided')

        self._filepath = filepath
        self._file = None

    def filepath(self):
        """
        Returns the filepath for this parser.

        >>> import inspect
        >>> this_file = inspect.getfile(inspect.currentframe())
        >>> parser = EIMParser(filepath = this_file)
        >>> parser.filepath() == this_file
        True
        """
        return self._filepath

    def open_file(self):
        """
        Opens the file at filepath and stores descriptor.

        >>> f = open('./test.txt', 'w')
        >>> f.close()
        >>> parser = EIMParser(filepath = './test.txt')
        >>> parser.open_file()
        True
        >>> parser._file.name
        './test.txt'
        >>> parser._file.closed
        False
        >>> parser.close_file()
        >>> import os
        >>> os.unlink(f.name)

        >>> parser = EIMParser(filepath = 'nothere.txt')
        >>> parser.open_file()
        False
        """
        try:
            self._file = open(self._filepath, 'r')
            return True
        except FileNotFoundError:
            return False

    def close_file(self):
        """
        Closes the file at filepath.

        >>> f = open('./test.txt', 'w')
        >>> f.close()
        >>> parser = EIMParser(filepath = './test.txt')
        >>> parser.open_file()
        True
        >>> parser.close_file()
        >>> parser._file.closed
        True
        >>> import os
        >>> os.unlink(f.name)
        """
        if not self._file.closed: self._file.close()

class EIMInfoParser(EIMParser):

    def __init__(self, filepath):
        """
        Initializes EIMInfoparser.
        """
        super().__init__(filepath)
        self._date = None
        self._timestamps = {}
        self._song_timestamps = {}
        self._songs = {}
        self._session_id = None

    def to_dict(self):
        """
        Assembles a dictionary of parsed data.

        >>> p = EIMInfoParser('./data/T2_S9999_1nfo.txt')
        >>> p.parse()
        >>> p.to_dict() == {'songs':{'order': ['R014', 'S001', 'S012']},'timestamps': {'START':'2012-12-20T12:57:39','TEST':'2012-12-20T12:58:04','END':'2012-12-20T13:05:29'},'session_id':9999}
        True
        """
        return {'songs':self._songs,'timestamps':self._timestamps,'session_id':self._session_id}

    def parse(self):
        """
        Parses all lines in an info file.

        >>> p = EIMInfoParser('./data/T2_S9999_1nfo.txt')
        >>> p.parse()
        >>> p._songs
        {'order': ['R014', 'S001', 'S012']}
        >>> p._date
        datetime.date(2012, 12, 20)
        >>> p._timestamps['START']
        '2012-12-20T12:57:39'
        >>> p._timestamps['TEST']
        '2012-12-20T12:58:04'
        >>> p._timestamps['END']
        '2012-12-20T13:05:29'
        >>> p._song_timestamps
        {0: '2012-12-20T12:58:37', 1: '2012-12-20T13:01:04', 2: '2012-12-20T13:03:19'}
        >>> p._file.closed
        True
        """
        try:
            self.open_file()
            lines = list(self._file)

            # Find date line and parse it first
            for line in lines:
                if re.search('DATE', line):
                    self.parse_line(line)
                    break

            # Parse all lines
            for line in lines:
                self.parse_line(line)

            # Parse session id
            match = re.search('T\d_S(\d{4})_.*.txt', self._filepath)
            if match:
                self._session_id = int(match.groups()[0])
            else:
                raise RuntimeWarning("No valid session id found in filename %s" % self._filepath)

        finally:
            if self._file and not self._file.closed:
                self.close_file()

    def parse_line(self, line):
        """
        Parses a line of text from an info file.

        >>> f = open('./test.txt', 'w')
        >>> f.close()
        >>> p = EIMInfoParser('./test.txt')
        >>> p.parse_line('SONGS , symbol "R014.wav-S001.wav-S012.wav" ;')
        >>> p._songs
        {'order': ['R014', 'S001', 'S012']}

        >>> p.parse_line('DATE , symbol "12-20-2012" ;')
        >>> p._date
        datetime.date(2012, 12, 20)

        >>> p.parse_line('START , symbol "12:57:39" ;')
        >>> p._timestamps['START']
        '2012-12-20T12:57:39'

        >>> p.parse_line('TEST , symbol "12:58:04" ;')
        >>> p._timestamps['TEST']
        '2012-12-20T12:58:04'

        >>> p.parse_line('END , symbol "13:05:29" ;')
        >>> p._timestamps['END']
        '2012-12-20T13:05:29'

        >>> p.parse_line('"song2" , symbol "13:01:04" ;')
        >>> p.parse_line('"song1" , symbol "12:58:37" ;')
        >>> p.parse_line('"song3" , symbol "13:03:19" ;')
        >>> p._song_timestamps
        {0: '2012-12-20T12:58:37', 1: '2012-12-20T13:01:04', 2: '2012-12-20T13:03:19'}
        """
        timestamp_tags = {'START', 'TEST', 'END'}
        match = re.search('"?(\w+)"? ,.*', line)

        if match:
            tag = match.groups()[0].upper()

            if tag == 'SONGS':
                self.parse_songs_line(line)

            elif tag == 'DATE':
                self.parse_date_line(line)

            elif tag in timestamp_tags:
                self.parse_timestamp_line(line)

            elif tag[:-1] == 'SONG':
                self.parse_song_timestamp_line(line)
        else:
            print('no match for "%s"' % line)


    def parse_songs_line(self, line):
        """
        Parses the 'SONGS' line from an info file. Returns a dictionary
        of the songs in order in which they were presented in the experiment.

        >>> f = open('./test.txt', 'w')
        >>> f.close()
        >>> p = EIMInfoParser('./test.txt')
        >>> p.parse_songs_line('SONGS , symbol "R014.wav-S001.wav-S012.wav" ;')
        >>> p._songs
        {'order': ['R014', 'S001', 'S012']}

        >>> p.parse_songs_line('no songs here')
        Traceback (most recent call last):
            ...
        RuntimeWarning: No songs found in song line in ./test.txt
        """
        regex = re.compile('([HRST]\d{3})')
        songs = regex.findall(line)
        if len(songs) == 0:
            raise RuntimeWarning("No songs found in song line in %s"
                    % self._filepath)
        self._songs = {"order":songs}

    def ensure_date_set(self, message):
        """
        Throws an exception if _date is not set.

        >>> f = open('./test.txt', 'w')
        >>> f.close()
        >>> p = EIMInfoParser('./test.txt')
        >>> p._date = None
        >>> p.ensure_date_set('set the date!')
        Traceback (most recent call last):
            ...
        RuntimeError: set the date!
        """
        if not self._date:
            raise RuntimeError(message)

    def parse_timestamp_line(self, line):
        """
        Parses a timestamp line from an info file. Returns a dictionary
        corresponding to the timestamp.

        >>> f = open('./test.txt', 'w')
        >>> f.close()
        >>> p = EIMInfoParser('./test.txt')
        >>> p._date = datetime.date(2013, 8, 14)
        >>> p.parse_timestamp_line('START , symbol "12:57:39" ;')
        >>> p._timestamps['START']
        '2013-08-14T12:57:39'

        >>> p.parse_timestamp_line('STRT , symbol "12:57:39" ;')
        Traceback (most recent call last):
            ...
        RuntimeError: No valid timestamp marker found in ./test.txt

        >>> p.parse_timestamp_line('START , symbol "12:5:39" ;')
        Traceback (most recent call last):
            ...
        RuntimeError: No valid timestamp found for START in ./test.txt

        >>> p._date = None
        >>> p.parse_timestamp_line('START , symbol "12:57:39" ;')
        Traceback (most recent call last):
            ...
        RuntimeError: Trying to parse timestamps before date is set in ./test.txt
        """
        self.ensure_date_set("Trying to parse timestamps before date is set in %s"
                    % self._filepath)

        tag_match = re.search('(START|TEST|END)', line)
        if not tag_match:
            raise RuntimeError("No valid timestamp marker found in %s"
                    % self._filepath)
        else:
            tag = tag_match.groups()[0]

        time_match = re.search('(\d{2}):(\d{2}):(\d{2})', line)

        if not time_match or len(time_match.groups()) != 3:
            raise RuntimeError("No valid timestamp found for %s in %s"
                    % (tag, self._filepath))
        else:
            (h, m, s) = time_match.groups()


        timestamp = datetime.datetime(
                self._date.year,
                self._date.month,
                self._date.day,
                int(h),
                int(m),
                int(s)
                )
        self._timestamps[tag] = timestamp.isoformat()

    def parse_song_timestamp_line(self, line):
        """
        Parses a *song* timestamp line from an info file and adds this timestamp to _song_timestamps.

        >>> f = open('./test.txt', 'w')
        >>> f.close()
        >>> p = EIMInfoParser('./test.txt')
        >>> p._date = datetime.date(2013, 8, 14)
        >>> p.parse_song_timestamp_line('"song2" , symbol "13:01:04" ;')
        >>> p.parse_song_timestamp_line('"song1" , symbol "12:58:37" ;')
        >>> p.parse_song_timestamp_line('"song3" , symbol "13:03:19" ;')
        >>> p._song_timestamps
        {0: '2013-08-14T12:58:37', 1: '2013-08-14T13:01:04', 2: '2013-08-14T13:03:19'}

        >>> p.parse_song_timestamp_line('"sng2" , symbol "12:57:39" ;')
        Traceback (most recent call last):
            ...
        RuntimeError: No valid song tag found in ./test.txt

        >>> p.parse_song_timestamp_line('"song2" , symbol "12:5:39" ;')
        Traceback (most recent call last):
            ...
        RuntimeError: No valid timestamp found for song 2 in ./test.txt

        >>> p._date = None
        >>> p.parse_song_timestamp_line('START , symbol "12:57:39" ;')
        Traceback (most recent call last):
            ...
        RuntimeError: Trying to parse song timestamps before date is set in ./test.txt
        """

        self.ensure_date_set("Trying to parse song timestamps before date is set in %s"
                    % self._filepath)

        song_match = re.search('song(\d)', line)
        if not song_match:
            raise RuntimeError("No valid song tag found in %s"
                    % self._filepath)
        else:
            song = song_match.groups()[0]

        time_match = re.search('(\d{2}):(\d{2}):(\d{2})', line)

        if not time_match or len(time_match.groups()) != 3:
            raise RuntimeError("No valid timestamp found for song %d in %s"
                    % (int(song), self._filepath))
        else:
            (h, m, s) = time_match.groups()


        timestamp = datetime.datetime(
                self._date.year,
                self._date.month,
                self._date.day,
                int(h),
                int(m),
                int(s)
                )
        self._song_timestamps[int(song)-1] = timestamp.isoformat()


    def parse_date_line(self, line):
        """
        Parses the date line from an info file. Sets self._date accordingly.

        >>> f = open('./test.txt', 'w')
        >>> f.close()
        >>> p = EIMInfoParser('./test.txt')
        >>> p.parse_date_line('DATE , symbol "12-20-2012" ;')
        >>> p._date
        datetime.date(2012, 12, 20)

        >>> p.parse_date_line('no date here')
        Traceback (most recent call last):
            ...
        RuntimeWarning: No date found in date line in ./test.txt
        """
        date_components = re.search('(\d{2})-(\d{2})-(\d{4})', line)
        if date_components:
            (month, day, year) = date_components.groups()
            self._date = datetime.date(int(year), int(month), int(day))
        else:
            raise RuntimeWarning("No date found in date line in %s"
                    % self._filepath)

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
