from eim_parser import EIMParser, EIMParsingError
import re, datetime, sys

class EIMInfoParser(EIMParser):

    def __init__(self, filepath, logger=None):
        """
        Initializes EIMInfoParser.
        """
        super().__init__(filepath, logger)
        self._date = None
        self._timestamps = {}
        self._song_timestamps = {}
        self._songs = {}

    def to_dict(self):
        """
        Assembles a dictionary of parsed data.

        >>> p = EIMInfoParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt')
        >>> p.parse()
        >>> p.to_dict() == {'songs':{'order': ['R014', 'S001', 'S012']},'timestamps': {'START':'2012-12-20T12:57:39','TEST':'2012-12-20T12:58:04','END':'2012-12-20T13:05:29'},'session_id':9999,'location':'Manila','terminal':2}
        True
        """
        return {'songs':self._songs,'timestamps':self._timestamps,'session_id':self._experiment_metadata['session_id'],'location':self._experiment_metadata['location'],'terminal':self._experiment_metadata['terminal']}

    def parse_line(self, line, number):
        """
        Parses a line of text from an info file.

        >>> f = open('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt', 'r')
        >>> f.close()
        >>> p = EIMInfoParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt')
        >>> p.parse_line('SONGS , symbol "R014.wav-S001.wav-S012.wav" ;', 4)
        >>> p._songs
        {'order': ['R014', 'S001', 'S012']}

        >>> p.parse_line('DATE , symbol "12-20-2012" ;', 5)
        >>> p._date
        datetime.date(2012, 12, 20)

        >>> p.parse_line('START , symbol "12:57:39" ;', 6)
        >>> p._timestamps['START']
        '2012-12-20T12:57:39'

        >>> p.parse_line('TEST , symbol "12:58:04" ;', 7)
        >>> p._timestamps['TEST']
        '2012-12-20T12:58:04'

        >>> p.parse_line('END , symbol "13:05:29" ;', 8)
        >>> p._timestamps['END']
        '2012-12-20T13:05:29'

        >>> p.parse_line('"song2" , symbol "13:01:04" ;', 9)
        >>> p.parse_line('"song1" , symbol "12:58:37" ;', 10)
        >>> p.parse_line('"song3" , symbol "13:03:19" ;', 11)
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
            raise EIMParsingError('Unprocessed line: %s:%d' % (self._filepath, number))

    def parse_songs_line(self, line):
        """
        Parses the 'SONGS' line from an info file. Returns a dictionary
        of the songs in order in which they were presented in the experiment.

        >>> f = open('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt', 'r')
        >>> f.close()
        >>> p = EIMInfoParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt')
        >>> p.parse_songs_line('SONGS , symbol "R014.wav-S001.wav-S012.wav" ;')
        >>> p._songs
        {'order': ['R014', 'S001', 'S012']}

        >>> p.parse_songs_line('no songs here')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: No songs found in song line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt
        """
        regex = re.compile('([HRST]\d{3})')
        songs = regex.findall(line)
        if len(songs) == 0:
            raise EIMParsingError("No songs found in song line: %s"
                    % self._filepath)
        self._songs = {"order":songs}

    def ensure_date_set(self, message):
        """
        Throws an exception if _date is not set.

        >>> p = EIMInfoParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt')
        >>> p._date = None
        >>> p.ensure_date_set(None)
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Date not parsed and set in ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt
        """
        if not self._date:
            raise EIMParsingError('Date not parsed and set in %s' % self._filepath)

    def parse_timestamp_line(self, line):
        """
        Parses a timestamp line from an info file. Returns a dictionary
        corresponding to the timestamp.

        >>> f = open('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt', 'r')
        >>> f.close()
        >>> p = EIMInfoParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt')
        >>> p._date = datetime.date(2013, 8, 14)
        >>> p.parse_timestamp_line('START , symbol "12:57:39" ;')
        >>> p._timestamps['START']
        '2013-08-14T12:57:39'

        >>> p.parse_timestamp_line('STRT , symbol "12:57:39" ;')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: No valid timestamp marker found in ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt

        >>> p.parse_timestamp_line('START , symbol "12:5:39" ;')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: No valid timestamp found for START in ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt
        """
        self.ensure_date_set("Trying to parse timestamps before date is set in %s"
                    % self._filepath)

        tag_match = re.search('(START|TEST|END)', line)
        if not tag_match:
            raise EIMParsingError("No valid timestamp marker found in %s"
                    % self._filepath)
        else:
            tag = tag_match.groups()[0]

        time_match = re.search('(\d{2}):(\d{2}):(\d{2})', line)

        if not time_match or len(time_match.groups()) != 3:
            raise EIMParsingError("No valid timestamp found for %s in %s"
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

        >>> f = open('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt', 'r')
        >>> f.close()
        >>> p = EIMInfoParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt')
        >>> p._date = datetime.date(2013, 8, 14)
        >>> p.parse_song_timestamp_line('"song2" , symbol "13:01:04" ;')
        >>> p.parse_song_timestamp_line('"song1" , symbol "12:58:37" ;')
        >>> p.parse_song_timestamp_line('"song3" , symbol "13:03:19" ;')
        >>> p._song_timestamps
        {0: '2013-08-14T12:58:37', 1: '2013-08-14T13:01:04', 2: '2013-08-14T13:03:19'}

        >>> p.parse_song_timestamp_line('"sng2" , symbol "12:57:39" ;')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: No valid song tag found in ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt

        >>> p.parse_song_timestamp_line('"song2" , symbol "12:5:39" ;')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: No valid timestamp found for song 2 in ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt
        """

        self.ensure_date_set("Trying to parse song timestamps before date is set in %s"
                    % self._filepath)

        song_match = re.search('song(\d)', line)
        if not song_match:
            raise EIMParsingError("No valid song tag found in %s"
                    % self._filepath)
        else:
            song = song_match.groups()[0]

        time_match = re.search('(\d{2}):(\d{2}):(\d{2})', line)

        if not time_match or len(time_match.groups()) != 3:
            raise EIMParsingError("No valid timestamp found for song %d in %s"
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

        >>> f = open('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt', 'r')
        >>> f.close()
        >>> p = EIMInfoParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt')
        >>> p.parse_date_line('DATE , symbol "12-20-2012" ;')
        >>> p._date
        datetime.date(2012, 12, 20)

        >>> p.parse_date_line('no date here')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: No date found in date line in ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_1nfo.txt
        """
        date_components = re.search('(\d{2})-(\d{2})-(\d{4})', line)
        if date_components:
            (month, day, year) = date_components.groups()
            self._date = datetime.date(int(year), int(month), int(day))
        else:
            raise EIMParsingError("No date found in date line in %s"
                    % self._filepath)

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
