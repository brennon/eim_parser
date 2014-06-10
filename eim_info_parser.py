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
        self._song_timestamps = []
        self._songs = {}

    def ensure_date_set(self, message):
        """
        Throws an exception if _date is not set.

        >>> f = open('./test_data/T1_MANILA_S9999_1nfo.txt', 'w')
        >>> f.close()

        >>> p = EIMInfoParser('./test_data/T1_MANILA_S9999_1nfo.txt')
        >>> p._date = None
        >>> p.ensure_date_set(None)
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/T1_MANILA_S9999_1nfo.txt')
        """
        if not self._date:
            raise EIMParsingError('Date not parsed and set in %s' % self._filepath)

    def to_dict(self):
        """
        Assembles a dictionary of parsed data.

        >>> p = EIMInfoParser('./test_data/SINGAPORE/SERVER/2012-07-20/SingaporeTerminal/T3/21-07-2012/experiment/T3_S0577_1nfo.txt')
        >>> p.parse()

        >>> p.to_dict()['media']
        ['H015.wav', 'S014.wav', 'H001.wav']

        >>> p.to_dict()['date']
        '2012-07-20'

        >>> p.to_dict()['timestamps']['start']
        '2012-07-20T14:25:58'

        >>> p.to_dict()['timestamps']['test']
        '2012-07-20T14:26:37'

        >>> p.to_dict()['timestamps']['end']
        '2012-07-20T14:34:36'

        >>> p.to_dict()['timestamps']['media'][0]
        '2012-07-20T14:27:08'

        >>> p.to_dict()['timestamps']['media'][1]
        '2012-07-20T14:29:54'

        >>> p.to_dict()['timestamps']['media'][2]
        '2012-07-20T14:32:19'

        >>> p.to_dict()['metadata']['session_number']
        577

        >>> p.to_dict()['metadata']['terminal']
        3

        >>> p.to_dict()['metadata']['location']
        'singapore'
        """
        all_timestamps = self._timestamps
        all_timestamps['media'] = self._song_timestamps

        return_dict = dict()
        return_dict['metadata'] = self._experiment_metadata
        return_dict['media'] = self._songs
        return_dict['timestamps'] = all_timestamps
        return_dict['date'] = self._date.isoformat()
        return return_dict

    def parse_line(self, line, number):
        """
        Parses a line of text from an info file.

        >>> f = open('./test_data/T1_MANILA_S9999_1nfo.txt', 'w')
        >>> f.close()

        >>> p = EIMInfoParser('./test_data/T1_MANILA_S9999_1nfo.txt')
        >>> p.parse_line('SONGS , symbol "R014.wav-S001.wav-S012.wav" ;', 4)
        >>> p._songs
        ['R014.wav', 'S001.wav', 'S012.wav']

        >>> p.parse_line('DATE , symbol "12-20-2012" ;', 5)
        >>> p._date
        datetime.date(2012, 12, 20)

        >>> p.parse_line('START , symbol "12:57:39" ;', 6)
        >>> p._timestamps['start']
        '2012-12-20T12:57:39'

        >>> p.parse_line('TEST , symbol "12:58:04" ;', 7)
        >>> p._timestamps['test']
        '2012-12-20T12:58:04'

        >>> p.parse_line('END , symbol "13:05:29" ;', 8)
        >>> p._timestamps['end']
        '2012-12-20T13:05:29'

        >>> p.parse_line('"song2" , symbol "13:01:04" ;', 9)
        >>> p.parse_line('"song1" , symbol "12:58:37" ;', 10)
        >>> p.parse_line('"song3" , symbol "13:03:19" ;', 11)
        >>> p._song_timestamps
        ['2012-12-20T12:58:37', '2012-12-20T13:01:04', '2012-12-20T13:03:19']

        >>> p = EIMInfoParser('./test_data/T1_MANILA_S9999_1nfo.txt')
        >>> p.parse_line('DATE, 08-05-2010;', 12)
        >>> p._date
        datetime.date(2010, 8, 5)

        >>> import os
        >>> os.unlink('./test_data/T1_MANILA_S9999_1nfo.txt')
        """
        timestamp_tags = {'START', 'TEST', 'END'}
        match = re.search('\"?(\w+)\"?\s?,?', line)

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

            elif re.search('^[HRST]\d{3}', tag):
                song_file = tag + ".wav"
                if self._songs and song_file in self._songs:
                    self.parse_song_timestamp_line(line)

        else:
            raise EIMParsingError('Unprocessed line: %s:%d' % (self._filepath, number))

    def parse_songs_line(self, line):
        """
        Parses the 'SONGS' line from an info file. Returns a dictionary
        of the songs in order in which they were presented in the experiment.

        >>> f = open('./test_data/T1_MANILA_S9999_1nfo.txt', 'w')
        >>> f.close()

        >>> p = EIMInfoParser('./test_data/T1_MANILA_S9999_1nfo.txt')
        >>> p.parse_songs_line('SONGS , symbol "R014.wav-S001.wav-S012.wav" ;')
        >>> p._songs
        ['R014.wav', 'S001.wav', 'S012.wav']

        >>> p._songs = None
        >>> p.parse_songs_line('SONGS , symbol "R014.wav-S012.wav" ;')
        >>> p._songs
        ['R014.wav', 'S012.wav']

        >>> p.parse_songs_line('no songs here')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/T1_MANILA_S9999_1nfo.txt')
        """
        regex = re.compile('([HRST]\d{3}.wav)')
        songs = regex.findall(line)
        if len(songs) == 0:
            raise EIMParsingError("No songs found in song line: %s"
                    % self._filepath)
        self._songs = songs

    def parse_timestamp_line(self, line):
        """
        Parses a timestamp line from an info file. Returns a dictionary
        corresponding to the timestamp.

        >>> f = open('./test_data/T1_MANILA_S9999_1nfo.txt', 'w')
        >>> f.close()

        >>> p = EIMInfoParser('./test_data/T1_MANILA_S9999_1nfo.txt')
        >>> p._date = datetime.date(2013, 8, 14)
        >>> p.parse_timestamp_line('START , symbol "12:57:39" ;')
        >>> p._timestamps['start']
        '2013-08-14T12:57:39'

        >>> p.parse_timestamp_line('TEST , symbol "12:57:40" ;')
        >>> p._timestamps['test']
        '2013-08-14T12:57:40'

        >>> p.parse_timestamp_line('END , symbol "12:57:41" ;')
        >>> p._timestamps['end']
        '2013-08-14T12:57:41'

        >>> p.parse_timestamp_line('STRT , symbol "12:57:39" ;')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> p.parse_timestamp_line('START , symbol "12:5:39" ;')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/T1_MANILA_S9999_1nfo.txt')
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
        self._timestamps[tag.lower()] = timestamp.isoformat()

    def parse_song_timestamp_line(self, line):
        """
        Parses a *song* timestamp line from an info file and adds this timestamp to _song_timestamps.

        >>> f = open('./test_data/T1_MANILA_S9999_1nfo.txt', 'w')
        >>> f.close()

        >>> p = EIMInfoParser('./test_data/T1_MANILA_S9999_1nfo.txt')
        >>> p._date = datetime.date(2013, 8, 14)
        >>> p.parse_song_timestamp_line('"song2" , symbol "13:01:04" ;')
        >>> p.parse_song_timestamp_line('"song1" , symbol "12:58:37" ;')
        >>> p.parse_song_timestamp_line('"song3" , symbol "13:03:19" ;')
        >>> p._song_timestamps
        ['2013-08-14T12:58:37', '2013-08-14T13:01:04', '2013-08-14T13:03:19']

        >>> p.parse_song_timestamp_line('"sng2" , symbol "12:57:39" ;')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> p.parse_song_timestamp_line('"song2" , symbol "12:5:39" ;')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> p = EIMInfoParser('./test_data/T1_MANILA_S9999_1nfo.txt')
        >>> p._date = datetime.date(2013, 8, 14)
        >>> p._songs = ['H006.wav','T001.wav','R010.wav']
        >>> p.parse_song_timestamp_line('T001, 17:29:38;')
        >>> p._song_timestamps[0]
        '2013-08-14T17:29:38'

        >>> import os
        >>> os.unlink('./test_data/T1_MANILA_S9999_1nfo.txt')
        """

        self.ensure_date_set("Trying to parse song timestamps before date is set in %s"
                    % self._filepath)

        song_match = re.search('song(\d)', line)
        direct_match = re.search('([HRST]\d{3})', line)

        if song_match:
            song = song_match.groups()[0]
        elif direct_match:
            song = direct_match.groups()[0]
        else:
            raise EIMParsingError("No valid song tag found in %s"
                    % self._filepath)


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
        self._song_timestamps.append(timestamp.isoformat())
        self._song_timestamps.sort()

    def parse_date_line(self, line):
        """
        Parses the date line from an info file. Sets self._date accordingly.

        >>> f = open('./test_data/T1_MANILA_S9999_1nfo.txt', 'w')
        >>> f.close()
        >>> p = EIMInfoParser('./test_data/T1_MANILA_S9999_1nfo.txt')
        >>> p.parse_date_line('DATE , symbol "12-20-2012" ;')
        >>> p._date
        datetime.date(2012, 12, 20)

        >>> p.parse_date_line('DATE, 08-05-2010;')
        >>> p._date
        datetime.date(2010, 8, 5)

        >>> p.parse_date_line('no date here')
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:
        >>> import os
        >>> os.unlink('./test_data/T1_MANILA_S9999_1nfo.txt')
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
    doctest.testmod(optionflags=doctest.IGNORE_EXCEPTION_DETAIL)

if __name__ == "__main__":
    __test()
