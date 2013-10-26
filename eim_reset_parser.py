from eim_parser import EIMParser, EIMParsingError
import re, datetime, sys, os

class EIMResetParser(EIMParser):
    def __init__(self, filepath, logger=None):
        """
        Initializes EIMResetParser.
        """
        super().__init__(filepath, logger)
        self.reset_slide = False

    def to_dict(self):
        """
        Assembles a dictionary of parsed data.

        >>> p = EIMResetParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T4_S0052_RESET.txt')
        >>> p.parse()
        >>> p.to_dict()['reset']
        True

        >>> p = EIMResetParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T4_S0054_RESET.txt')
        >>> p.parse()
        >>> p.to_dict()['reset']
        'Slide 11 Black1.maxpat'
        """
        data = {
            'session_id':self._experiment_metadata['session_id'],
            'terminal':self._experiment_metadata['terminal'],
            'location':self._experiment_metadata['location'],
            'reset':self.reset_slide}
        return data

    def parse(self):
        """
        Parses all text from a reset file.

        >>> p = EIMResetParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T4_S0052_RESET.txt')
        >>> p.parse()
        >>> p.reset_slide == True
        True

        >>> p = EIMResetParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T4_S0054_RESET.txt')
        >>> p.parse()
        >>> p.reset_slide == 'Slide 11 Black1.maxpat'
        True
        """
        try:
            self.open_file()
            lines = list(self._file)

            if len(lines) > 0:
                text = ''.join(lines)
                match = re.search("(Slide.*)", text, re.M)

                if match:
                    self.reset_slide = match.groups()[0].strip()
                else:
                    raise EIMParsingError('Malformed reset file: %s' % self._filepath)

            else:
                self.reset_slide = True

        finally:
            if self._file and not self._file.closed:
                self.close_file()

        match = re.search('T\d_S(\d+)_.*.txt', self._filepath)
        if match:
            self._experiment_metadata['session_id'] = int(match.groups()[0])
        else:
            raise EIMParsingError("No valid session id found in filename %s" % self._filepath)

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
