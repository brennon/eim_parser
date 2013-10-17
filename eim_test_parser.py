from eim_parser import EIMParser, EIMParserLogger, EIMParsingError, timestamp_to_millis
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

        >>> p = EIMTestParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_TEST.txt')
        >>> p.parse()
        >>> len(p.to_dict()['signals']['test']['timestamps'])
        1497
        >>> len(p.to_dict()['signals']['test']['eda_raw'])
        1497
        >>> len(p.to_dict()['signals']['test']['eda_filtered'])
        1497
        >>> len(p.to_dict()['signals']['test']['eda_status'])
        1497
        >>> len(p.to_dict()['signals']['test']['pox_raw'])
        1497
        >>> len(p.to_dict()['signals']['test']['hr'])
        1497
        >>> len(p.to_dict()['signals']['test']['hr_status'])
        1497
        """
        data = {
            'session_id':self._experiment_metadata['session_id'],
            'terminal':self._experiment_metadata['terminal'],
            'location':self._experiment_metadata['location'],
            'signals': {
                'test': {
                    'timestamps':self._timestamps,
                    'eda_raw':self._eda_raw,
                    'eda_filtered':self._eda_filtered,
                    'eda_status':self._eda_status,
                    'pox_raw':self._pox_raw,
                    'hr':self._hr,
                    'hr_status':self._hr_status}}}
        return data

    def parse_line(self, line, number):
        """
        Parses a line of text from an test file.

        >>> f = open('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_TEST.txt', 'r')
        >>> f.close()
        >>> p = EIMTestParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_TEST.txt')
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
        >>> p.parse_line('00:00.000 143 145.000 1 0 72.289', 3)
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Malformed line in './data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S9999_TEST.txt:3': 00:00.000 143 145.000 1 0 72.289
        """
        match = re.search('(\\d+:\\d+.\\d+) (\\d+) (\\d+.\\d+) (\\d+) (\\d+) (\\d+.\\d+) (\\d+)', line)
        if match and len(match.groups()) == 7:
            self._timestamps.append(timestamp_to_millis(match.groups()[0]))
            self._eda_raw.append(float(match.groups()[1]))
            self._eda_filtered.append(float(match.groups()[2]))
            self._eda_status.append(int(match.groups()[3]))
            self._pox_raw.append(float(match.groups()[4]))
            self._hr.append(float(match.groups()[5]))
            self._hr_status.append(int(match.groups()[6]))
        else:
            self.logger.log('Malformed line in \'%s:%d\': %s' % (self._filepath, number, line), 'WARN')
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

        >>> p = EIMSongParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_R014.txt')
        >>> p.parse()
        >>> len(p.to_dict()['signals']['songs']['R014']['timestamps'])
        22722
        >>> len(p.to_dict()['signals']['songs']['R014']['eda_raw'])
        22722
        >>> len(p.to_dict()['signals']['songs']['R014']['eda_filtered'])
        22722
        >>> len(p.to_dict()['signals']['songs']['R014']['eda_status'])
        22722
        >>> len(p.to_dict()['signals']['songs']['R014']['pox_raw'])
        22722
        >>> len(p.to_dict()['signals']['songs']['R014']['hr'])
        22722
        >>> len(p.to_dict()['signals']['songs']['R014']['hr_status'])
        22722
        """
        match = re.search('/T\d+_.*_(.*).txt', self._filepath)
        if match:
            data = {
                'session_id':self._experiment_metadata['session_id'],
                'terminal':self._experiment_metadata['terminal'],
                'location':self._experiment_metadata['location'],
                'signals': {
                    'songs': {}}}
            data['signals']['songs'][match.groups()[0]] = {
                'timestamps':self._timestamps,
                'eda_raw':self._eda_raw,
                'eda_filtered':self._eda_filtered,
                'eda_status':self._eda_status,
                'pox_raw':self._pox_raw,
                'hr':self._hr,
                'hr_status':self._hr_status}
            return data
        else:
            self.logger.log("Could not find a valid song label in %s" % self._filepath, 'WARN')
            raise EIMParsingError("Could not find a valid song label in %s" % self._filepath, 'WARN')

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
