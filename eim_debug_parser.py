from eim_parser import EIMParser, EIMParsingError
import re, datetime, sys, os

class EIMDebugParser(EIMParser):
    def __init__(self, filepath, logger=None):
        """
        Initializes EIMDebugParser.
        """
        super().__init__(filepath, logger)
        self.debug_data = []

    def to_dict(self):
        """
        Assembles a dictionary of parsed data.

        >>> p = EIMDebugParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_debug.txt')
        >>> p.parse()
        >>> debug_dict = p.to_dict()
        >>> debug_dict['debug'][1] == {'start':'13:01:04','length':95628.719,'end':'13:02:40'}
        True

        >>> f = open('./.MANILA_T2_S9999_debug.txt', 'w')
        >>> f.close()
        >>> p = EIMDebugParser('./.MANILA_T2_S9999_debug.txt')
        >>> p.parse()
        >>> debug_dict = p.to_dict()
        >>> debug_dict['debug'] == []
        True
        >>> os.unlink(f.name)
        """
        data = {
            'session_id':self._experiment_metadata['session_id'],
            'terminal':self._experiment_metadata['terminal'],
            'location':self._experiment_metadata['location'],
            'debug':self.debug_data}
        return data

    def parse(self):
        """
        Parses all text from a debug file.

        >>> p = EIMDebugParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_debug.txt')
        >>> p.parse()
        >>> p.debug_data[1] == {'start':'13:01:04','length':95628.719,'end':'13:02:40'}
        True

        >>> p = EIMDebugParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T1_S0127_debug.txt')
        >>> p.parse()
        >>> p.debug_data[0] == {'start':'06:27:50','length':119193.914,'end':'06:29:49'}
        True
        >>> len(p.debug_data)
        1

        >>> p = EIMDebugParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T1_S0214_debug.txt')
        >>> p.parse()
        >>> p.debug_data[0] == {'start':'12:33:27','length':90792.594,'end':'12:34:57'}
        True
        >>> p.debug_data[1] == {'start':'13:40:41','length':84937.313,'end':'13:42:06'}
        True
        >>> len(p.debug_data)
        2

        >>> p = EIMDebugParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0275_debug.txt')
        >>> p.parse()
        >>> p.debug_data == []
        True

        >>> f = open('./.MANILA_T2_S9999_debug.txt', 'w')
        >>> f.close()
        >>> p = EIMDebugParser('./.MANILA_T2_S9999_debug.txt')
        >>> p.parse()
        >>> os.unlink(f.name)
        """
        try:
            self.open_file()
            lines = list(self._file)

            if len(lines) > 0:
                text = ''.join(lines)
                regex = 'Song \d+\nStart (\d+:\d+:\d+)\nEnd (\d+:\d+:\d+)\nLength (\d+.\d+)'
                match = re.findall(regex, text)
                if len(match):
                    starts = []
                    ends = []
                    lengths = []

                    for i in range(len(match)):
                        starts.append(match[i][0])
                        ends.append(match[i][1])
                        lengths.append(float(match[i][2]))

                    for i in range(len(match)):
                        self.debug_data.append({
                            'start':starts[i],'end':ends[i],'length':lengths[i]})

                match = re.search('T\d_S(\d{4})_.*.txt', self._filepath)
                if match:
                    self._experiment_metadata['session_id'] = int(match.groups()[0])
                else:
                    raise EIMParsingError("No valid session id found in filename %s" % self._filepath)

        finally:
            if self._file and not self._file.closed:
                self.close_file()

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
