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

        >>> p = EIMResetParser('./eim_parser/test_data/SINGAPORE/SERVER/2012-07-20/SingaporeTerminal/T3/21-07-2012/experiment/T3_S0582_RESET.txt')
        >>> p.parse()
        >>> p.to_dict()['reset']
        True
        >>> p.to_dict()['metadata']['location']
        'singapore'
        >>> p.to_dict()['metadata']['session_number']
        582
        >>> p.to_dict()['metadata']['terminal']
        3

        >>> p = EIMResetParser('./test_data/SINGAPORE/SERVER/2012-07-20/SingaporeTerminal/T3/21-07-2012/experiment/T3_S0576_RESET.txt')
        >>> p.parse()
        >>> p.to_dict()['reset']
        'Slide 11 Black1.maxpat'
        >>> p.to_dict()['metadata']['location']
        'singapore'
        >>> p.to_dict()['metadata']['session_number']
        576
        >>> p.to_dict()['metadata']['terminal']
        3
        """
        if not self._experiment_metadata['session_number']:
            raise EIMParsingError('No session ID for reset file: %s' % self._filepath)

        base = super().to_dict()
        base['reset'] = self.reset_slide
        return base

    def parse(self):
        """
        Parses all text from a reset file.

        >>> p = EIMResetParser('./eim_parser/test_data/SINGAPORE/SERVER/2012-07-20/SingaporeTerminal/T3/21-07-2012/experiment/T3_S0582_RESET.txt')
        >>> p.parse()
        >>> p.reset_slide == True
        True

        >>> p = EIMResetParser('./test_data/SINGAPORE/SERVER/2012-07-20/SingaporeTerminal/T3/21-07-2012/experiment/T3_S0576_RESET.txt')
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

        except:
            self.reset_slide = True

        finally:
            if self._file and not self._file.closed:
                self.close_file()

        match = re.search('T\d_S(\d+)_.*.txt', self._filepath)
        if match:
            self._experiment_metadata['session_number'] = int(match.groups()[0])
        else:
            raise EIMParsingError("No valid session id found in filename %s" % self._filepath)

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
