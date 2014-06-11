from eim_parser import EIMParser, EIMParsingError, timestamp_to_millis
import re, datetime, sys

class EIMTestParser(EIMParser):
    def __init__(self, filepath, logger=None):
        """
        Initializes EIMTestParser.
        """
        super().__init__(filepath, logger)
        self._timestamps = []
        self._eda_raw = []
        self._eda_filtered = []
        self._eda_status = []
        self._pox_raw = []
        self._hr = []
        self._hr_status = []

    def to_dict(self):
        """
        Assembles a dictionary of parsed data.

        >>> p = EIMTestParser('./test_data/SINGAPORE/SERVER/2012-07-20/SingaporeTerminal/T3/21-07-2012/experiment/T3_S0576_TEST.txt')
        >>> p.parse()
        >>> len(p.to_dict()['signals']['timestamps'])
        1499
        >>> len(p.to_dict()['signals']['eda_raw'])
        1499
        >>> len(p.to_dict()['signals']['eda_filtered'])
        1499
        >>> len(p.to_dict()['signals']['eda_status'])
        1499
        >>> len(p.to_dict()['signals']['pox_raw'])
        1499
        >>> len(p.to_dict()['signals']['hr'])
        1499
        >>> len(p.to_dict()['signals']['hr_status'])
        1499
        >>> p.to_dict()['label']
        'test'
        >>> p.to_dict()['signals']['timestamps'][17]
        0
        >>> p.to_dict()['signals']['eda_raw'][17]
        279.0
        >>> p.to_dict()['signals']['eda_filtered'][17]
        280.15
        >>> p.to_dict()['signals']['eda_status'][17]
        1
        >>> p.to_dict()['signals']['pox_raw'][17]
        974.0
        >>> p.to_dict()['signals']['hr'][17]
        71.429
        >>> p.to_dict()['signals']['hr_status'][17]
        1
        >>> p.to_dict()['metadata']['location']
        'singapore'
        >>> p.to_dict()['metadata']['terminal']
        3
        >>> p.to_dict()['metadata']['session_number']
        576
        """
        data = {
            'metadata':self._experiment_metadata,
            'signals': {
                'timestamps':self._timestamps,
                'eda_raw':self._eda_raw,
                'eda_filtered':self._eda_filtered,
                'eda_status':self._eda_status,
                'pox_raw':self._pox_raw,
                'hr':self._hr,
                'hr_status':self._hr_status
            },
            'label':'test'
        }
        return data

    def parse_line(self, line, number):
        """
        Parses a line of text from an test file.

        >>> f = open('./test_data/.T1_MANILA_S9999_TEST.txt', 'w')
        >>> f.close()

        >>> p = EIMTestParser('./test_data/DUBLIN/MuSE_SERVER/05-Sep-2010/T1_S0941_H003.txt')
        >>> p.parse_line('00:00.000 343 503 0 0 0 0 0 0 0 0 0 0 0 0', 1)
        >>> p.parse_line('00:00.000 343 496 0 0 0 0 0 0 0 0 0 0 0 0', 2)
        >>> p._timestamps[0]
        0
        >>> p._timestamps[1]
        0
        >>> p._eda_raw[0]
        343.0
        >>> p._eda_raw[1]
        343.0
        >>> p._pox_raw[0]
        503.0
        >>> p._pox_raw[1]
        496.0

        >>> p.parse_line('00:00.000 143 145.000 1 0 72.289', 3)
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> p = EIMTestParser('./test_data/.T1_MANILA_S9999_TEST.txt')
        >>> p.parse_line('00:00.000 143 145.000 1 0 72.289 1', 1)
        >>> p.parse_line('00:00.001 144 146.000 0 1 73.289 0', 2)
        >>> p._timestamps[0]
        0
        >>> p._timestamps[1]
        1
        >>> p._eda_raw[1]
        144.0
        >>> p._eda_filtered[1]
        146.0
        >>> p._eda_status[1]
        0
        >>> p._pox_raw[1]
        1.0
        >>> p._hr[1]
        73.289
        >>> p._hr_status[1]
        0

        >>> import os
        >>> os.unlink('./test_data/.T1_MANILA_S9999_TEST.txt')
        """
        match = re.search('(\d+:\d+.\d+)\s(\d+)\s(\d+\.?\d*)\s(\d*)\s(\d*) (\d+\.?\d*)\s(\d*)', line)
        if match and len(match.groups()) == 7 and self.version > 4:
            self._timestamps.append(timestamp_to_millis(match.groups()[0]))
            self._eda_raw.append(float(match.groups()[1]))
            self._eda_filtered.append(float(match.groups()[2]))
            self._eda_status.append(int(match.groups()[3]))
            self._pox_raw.append(float(match.groups()[4]))
            self._hr.append(float(match.groups()[5]))
            self._hr_status.append(int(match.groups()[6]))
        elif match and len(match.groups()) == 7 and self.version <= 4:
            self._timestamps.append(timestamp_to_millis(match.groups()[0]))
            self._eda_raw.append(float(match.groups()[1]))
            self._pox_raw.append(float(match.groups()[2]))
        else:
            raise EIMParsingError('Malformed line in \'%s:%d\': %s' % (self._filepath, number, line))

class EIMSongParser(EIMTestParser):
    def __init__(self, filepath, logger=None):
        """
        Initializes EIMTestParser.
        """
        super().__init__(filepath, logger)

    def to_dict(self):
        """
        Assembles a dictionary of parsed data.

        >>> p = EIMSongParser('./test_data/SINGAPORE/SERVER/2012-07-20/SingaporeTerminal/T3/21-07-2012/experiment/T3_S0574_R017.txt')
        >>> p.parse()
        >>> len(p.to_dict()['signals']['timestamps'])
        19867
        >>> len(p.to_dict()['signals']['eda_raw'])
        19867
        >>> len(p.to_dict()['signals']['eda_filtered'])
        19867
        >>> len(p.to_dict()['signals']['eda_status'])
        19867
        >>> len(p.to_dict()['signals']['pox_raw'])
        19867
        >>> len(p.to_dict()['signals']['hr'])
        19867
        >>> len(p.to_dict()['signals']['hr_status'])
        19867
        >>> p.to_dict()['signals']['timestamps'][19866]
        79573
        >>> p.to_dict()['signals']['eda_raw'][19866]
        338.0
        >>> p.to_dict()['signals']['eda_filtered'][19866]
        340.85
        >>> p.to_dict()['signals']['eda_status'][19866]
        1
        >>> p.to_dict()['signals']['pox_raw'][19866]
        0.0
        >>> p.to_dict()['signals']['hr'][19866]
        75.949
        >>> p.to_dict()['signals']['hr_status'][19866]
        1
        >>> p.to_dict()['metadata']['location']
        'singapore'
        >>> p.to_dict()['metadata']['terminal']
        3
        >>> p.to_dict()['metadata']['session_number']
        574
        >>> p.to_dict()['label']
        'R017'

        """
        match = re.search('/T\d+_.*_(.*).txt', self._filepath)
        if match:
            return {
                'metadata':self._experiment_metadata,
                'label':match.groups()[0],
                'signals': {
                    'timestamps':self._timestamps,
                    'eda_raw':self._eda_raw,
                    'eda_filtered':self._eda_filtered,
                    'eda_status':self._eda_status,
                    'pox_raw':self._pox_raw,
                    'hr':self._hr,
                    'hr_status':self._hr_status
                }
            }
        else:
            raise EIMParsingError("Could not find a valid song label in %s" % self._filepath)

def __test():
    import doctest
    doctest.testmod(optionflags=doctest.IGNORE_EXCEPTION_DETAIL)

if __name__ == "__main__":
    __test()
