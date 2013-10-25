from eim_parser import EIMParser, EIMParsingError
import re, datetime, sys

class EIMAnswersParser(EIMParser):

    def __init__(self, filepath, logger=None):
        """
        Initializes EIMAnswersParser.
        """
        super().__init__(filepath, logger)
        self.sex = None
        self.dob = None
        self.nationality = None
        self.musical_background = None
        self.musical_expertise = None
        self.hearing_impairments = None
        self.visual_impairments = None
        self.song_scales = None
        self.most_enjoyed = None
        self.most_engaged = None
        self.emotion_indices = None
        self.music_styles = None

    def to_dict(self):
        """
        Assembles a dictionary of parsed data.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse()
        >>> out_dict = p.to_dict()['questionnaire']
        >>> out_dict['sex']
        'Female'
        >>> out_dict['dob']
        1983
        >>> out_dict['nationality']
        'Filipino'
        >>> out_dict['musical_background']
        False
        >>> out_dict['musical_expertise']
        3
        >>> out_dict['hearing_impairments']
        False
        >>> out_dict['visual_impairments']
        False
        >>> out_dict['most_engaged']
        1
        >>> out_dict['most_enjoyed']
        1
        >>> 'pop' in out_dict['music_styles'] and 'jazz' in out_dict['music_styles'] and 'dance' in out_dict['music_styles'] and 'hip_hop' in out_dict['music_styles'] and 'none' not in out_dict['music_styles']
        True
        >>> out_dict['emotion_indices']
        [21.4085, 0.59521, 0.598997]
        """
        answers_dict = {'session_id':self._experiment_metadata['session_id'],
            'terminal':self._experiment_metadata['terminal'],
            'location':self._experiment_metadata['location'],
            'questionnaire':{
                'sex':self.sex,
                'dob':self.dob,
                'nationality':self.nationality,
                'musical_background':self.musical_background,
                'musical_expertise':self.musical_expertise,
                'hearing_impairments':self.hearing_impairments,
                'visual_impairments':self.visual_impairments,
                'most_engaged':self.most_engaged,
                'most_enjoyed':self.most_enjoyed,
                'music_styles':[],
                'emotion_indices':[]}}

        for key in self.music_styles.keys():
            if self.music_styles[key]:
                answers_dict['questionnaire']['music_styles'].append(key)

        try:
            indices = list(self.emotion_indices.keys())
            indices.sort()
            for i in indices:
                answers_dict['questionnaire']['emotion_indices'].append(self.emotion_indices[i])
        except:
            pass

        return answers_dict

    def parse_line(self, line, number):
        """
        Parses a line of text from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_line('"01a_Sex , symbol Female ;', 1)
        >>> p.sex
        'Female'

        >>> p.parse_line('"01b_DOB" , 1983 ;', 2)
        >>> p.dob
        1983

        >>> p.parse_line('"02_Nationality" , symbol Filipino ;', 3)
        >>> p.nationality
        'Filipino'

        >>> p.parse_line('"03_Musical_Background" , symbol No ;', 4)
        >>> p.musical_background
        False

        >>> p.parse_line('"03_Musical_Expertise" , 3 ;', 5)
        >>> p.musical_expertise
        3

        >>> p.parse_line('"04_Hearing_Impairments" , symbol No ;', 6)
        >>> p.hearing_impairments
        False

        >>> p.parse_line('"04_Visual_Impairments" , symbol No ;', 7)
        >>> p.visual_impairments
        False

        >>> p.parse_line('"Song1_Scale1_Engagement" , 3 ;', 8)
        >>> p.song_scales['1']['engagement']
        3

        >>> p.parse_line('"Song1_Scale2_Positivity" , 3 ;', 9)
        >>> p.song_scales['1']['positivity']
        3

        >>> p.parse_line('"Song1_Scale3_Activity" , 2 ;', 10)
        >>> p.song_scales['1']['activity']
        2

        >>> p.parse_line('"Song1_Scale4_Power" , 3 ;', 11)
        >>> p.song_scales['1']['power']
        3

        >>> p.parse_line('"Song1_Scale5_Chills" , 1 ;', 12)
        >>> p.song_scales['1']['chills']
        1

        >>> p.parse_line('"Song1_Scale6_like_dislike" , 2 ;', 13)
        >>> p.song_scales['1']['like_dislike']
        2

        >>> p.parse_line('"Song1_Scale7_Familiarity" , 4 ;', 14)
        >>> p.song_scales['1']['familiarity']
        4

        >>> p.parse_line('"Song2_Scale1_Engagement" , 1 ;', 15)
        >>> p.song_scales['2']['engagement']
        1

        >>> p.parse_line('"Song2_Scale2_Positivity" , 2 ;', 16)
        >>> p.song_scales['2']['positivity']
        2

        >>> p.parse_line('"Song2_Scale3_Activity" , 1 ;', 17)
        >>> p.song_scales['2']['activity']
        1

        >>> p.parse_line('"Song2_Scale4_Power" , 3 ;', 18)
        >>> p.song_scales['2']['power']
        3

        >>> p.parse_line('"Song2_Scale5_Chills" , 1 ;', 19)
        >>> p.song_scales['2']['chills']
        1

        >>> p.parse_line('"Song2_Scale6_like_dislike" , 1 ;', 20)
        >>> p.song_scales['2']['like_dislike']
        1

        >>> p.parse_line('"Song2_Scale7_Familiarity" , 1 ;', 21)
        >>> p.song_scales['2']['familiarity']
        1

        >>> p.parse_line('"Song3_Scale1_Engagement" , 2 ;', 22)
        >>> p.song_scales['3']['engagement']
        2

        >>> p.parse_line('"Song3_Scale2_Positivity" , 3 ;', 23)
        >>> p.song_scales['3']['positivity']
        3

        >>> p.parse_line('"Song3_Scale3_Activity" , 2 ;', 24)
        >>> p.song_scales['3']['activity']
        2

        >>> p.parse_line('"Song3_Scale4_Power" , 3 ;', 25)
        >>> p.song_scales['3']['power']
        3

        >>> p.parse_line('"Song3_Scale5_Chills" , 1 ;', 26)
        >>> p.song_scales['3']['chills']
        1

        >>> p.parse_line('"Song3_Scale6_like_dislike" , 2 ;', 27)
        >>> p.song_scales['3']['like_dislike']
        2

        >>> p.parse_line('"Song3_Scale7_Familiarity" , 1 ;', 28)
        >>> p.song_scales['3']['familiarity']
        1

        >>> p.parse_line('FinalQ_Most_Engaged , 1 ;', 29)
        >>> p.most_engaged
        1

        >>> p.parse_line('FinalQ_Most_Enjoyed , 1 ;', 30)
        >>> p.most_enjoyed
        1

        >>> p.parse_line('"EmotionIndex3" , 0.598997 ;', 31)
        >>> p.emotion_indices['3']
        0.598997

        >>> p.parse_line('"EmotionIndex2" , 0.595210 ;', 32)
        >>> p.emotion_indices['2']
        0.59521

        >>> p.parse_line('"EmotionIndex1" , 21.4085 ;', 33)
        >>> p.emotion_indices['1']
        21.4085

        >>> p.parse_line('"05_Music_Style_None" , 0 ;', 34)
        >>> p.music_styles['none']
        False

        >>> p.parse_line('"05_Music_Style_Pop" , 1 ;', 35)
        >>> p.music_styles['pop']
        True

        >>> p.parse_line('"05_Music_Style_Jazz" , 1 ;', 36)
        >>> p.music_styles['jazz']
        True

        >>> p.parse_line('"05_Music_Style_Dance" , 1 ;', 37)
        >>> p.music_styles['dance']
        True

        >>> p.parse_line('"05_Music_Style_Hip_Hop" , 1 ;', 38)
        >>> p.music_styles['hip_hop']
        True

        >>> p.parse_line('SOME CRAZY LINE', 98) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Unprocessed line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:98 SOME CRAZY LINE
        """
        if re.search('SEX', line.upper()):
            self.parse_sex_line(line, number)

        elif re.search('DOB', line.upper()):
            self.parse_dob_line(line, number)

        elif re.search('NATIONALITY', line.upper()):
            self.parse_nationality_line(line, number)

        elif re.search('MUSICAL_BACKGROUND', line.upper()):
            self.parse_musical_background_line(line, number)

        elif re.search('MUSICAL_EXPERTISE', line.upper()):
            self.parse_musical_expertise_line(line, number)

        elif re.search('HEARING_IMPAIRMENTS', line.upper()):
            self.parse_hearing_impairments_line(line, number)

        elif re.search('VISUAL_IMPAIRMENTS', line.upper()):
            self.parse_visual_impairments_line(line, number)

        elif re.search('SONG\d+_SCALE\d+', line.upper()):
            self.parse_song_scale_line(line, number)

        elif re.search('FINALQ_MOST', line.upper()):
            self.parse_most_enjoyed_engaged_line(line, number)

        elif re.search('EMOTIONINDEX', line.upper()):
            self.parse_emotion_index_line(line, number)

        elif re.search('MUSIC_?STYLE', line.upper()):
            self.parse_music_style_line(line, number)

        else:
            raise EIMParsingError('Unprocessed line: %s:%d %s' % (self._filepath, number, line))

    def parse_most_enjoyed_engaged_line(self, line, number):
        """
        Parses the 'Most Enjoyed / Engaged' lines from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_most_enjoyed_engaged_line('FinalQ_Most_Enjoyed , 3 ;', 1)
        >>> p.most_enjoyed
        3

        >>> p.parse_most_enjoyed_engaged_line('FinalQ_Most_Engaged , 4 ;', 1)
        >>> p.most_engaged
        4

        >>> p.parse_most_enjoyed_engaged_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid most enjoyed / engaged line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search('FinalQ_Most_(\w+) , (\d+) ;', line)
        if match:
            if match.groups()[0] == 'Enjoyed':
                self.most_enjoyed = int(match.groups()[1])
            elif match.groups()[0] == 'Engaged':
                self.most_engaged = int(match.groups()[1])
        else:
            raise EIMParsingError("Invalid most enjoyed / engaged line: %s:%d"
                    % (self._filepath, number))

    def parse_musical_expertise_line(self, line, number):
        """
        Parses the 'Musical Expertise' line from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_musical_expertise_line('"03_Musical_Expertise" , 3 ;', 1)
        >>> p.musical_expertise
        3

        >>> p.parse_musical_expertise_line('"03_Musical_Expertise" , symbol Lots ;', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid musical expertise line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search(', (\d+) ;', line)
        if match:
            self.musical_expertise = int(match.groups()[0])
        else:
            raise EIMParsingError("Invalid musical expertise line: %s:%d"
                    % (self._filepath, number))

    def parse_music_style_line(self, line, number):
        """
        Parses an 'Music Style' line from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_music_style_line('"05_Music_Style_Pop" , 1 ;', 1)
        >>> p.music_styles['pop']
        True

        >>> p.parse_music_style_line('"05_Music_Style_None" , 0 ;', 1)
        >>> p.music_styles['none']
        False

        >>> p.parse_music_style_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid music style line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search('".+Style_(\w+)" , (\d) ;', line)
        if match:
            style = match.groups()[0].lower()
            value = None
            if match.groups()[1] == '1':
                value = True
            else:
                value = False
            if not self.music_styles:
                self.music_styles = dict()
            self.music_styles[style] = value
        else:
            raise EIMParsingError("Invalid music style line: %s:%d"
                    % (self._filepath, number))

    def parse_emotion_index_line(self, line, number):
        """
        Parses an 'Emotion Index' line from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_emotion_index_line('"EmotionIndex2" , 36.4641 ;', 1)
        >>> p.emotion_indices['2']
        36.4641

        >>> p.parse_emotion_index_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid emotion index line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search('"EmotionIndex(\w+)" , (\d+\.\d+) ;', line)
        if match:
            if not self.emotion_indices:
                self.emotion_indices = dict()
            number = match.groups()[0]
            value = float(match.groups()[1])
            self.emotion_indices[number] = value
        else:
            raise EIMParsingError("Invalid emotion index line: %s:%d"
                    % (self._filepath, number))

    def parse_song_scale_line(self, line, number):
        """
        Parses a 'Song Scale' line from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_song_scale_line('"Song2_Scale4_Power" , 5 ;', 1)
        >>> p.song_scales['2']['power']
        5

        >>> p.parse_song_scale_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid song scale line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search('"Song(\d+)_Scale\d+_(\w+)" , (\d+) ;', line)
        if match:
            if not self.song_scales:
                self.song_scales = dict()
            number = match.groups()[0]
            scale = match.groups()[1].lower()
            value = int(match.groups()[2])
            if number not in self.song_scales:
                self.song_scales[number] = dict()
            self.song_scales[match.groups()[0]][scale] = value
        else:
            raise EIMParsingError("Invalid song scale line: %s:%d"
                    % (self._filepath, number))

    def parse_visual_impairments_line(self, line, number):
        """
        Parses the 'Hearing Impairments' line from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_visual_impairments_line('"04_Visual_Impairments" , symbol Yes ;', 1)
        >>> p.visual_impairments
        True

        >>> p.parse_visual_impairments_line('"04_Visual_Impairments" , symbol No ;', 1)
        >>> p.visual_impairments
        False

        >>> p.parse_visual_impairments_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid visual impairments line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search('(Yes|No)', line)
        if match:
            if match.groups()[0] == 'Yes':
                self.visual_impairments = True
            else:
                self.visual_impairments = False
        else:
            raise EIMParsingError("Invalid visual impairments line: %s:%d"
                    % (self._filepath, number))

    def parse_hearing_impairments_line(self, line, number):
        """
        Parses the 'Hearing Impairments' line from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_hearing_impairments_line('"04_Hearing_Impairments" , symbol Yes ;', 1)
        >>> p.hearing_impairments
        True

        >>> p.parse_hearing_impairments_line('"04_Hearing_Impairments" , symbol No ;', 1)
        >>> p.hearing_impairments
        False

        >>> p.parse_hearing_impairments_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid hearing impairments line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search('(Yes|No)', line)
        if match:
            if match.groups()[0] == 'Yes':
                self.hearing_impairments = True
            else:
                self.hearing_impairments = False
        else:
            raise EIMParsingError("Invalid hearing impairments line: %s:%d"
                    % (self._filepath, number))

    def parse_musical_background_line(self, line, number):
        """
        Parses the 'Musical Background' line from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_musical_background_line('"03_Musical_Background" , symbol Yes ;', 1)
        >>> p.musical_background
        True

        >>> p.parse_musical_background_line('"03_Musical_Background" , symbol No ;', 1)
        >>> p.musical_background
        False

        >>> p.parse_musical_background_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid musical background line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search('(Yes|No)', line)
        if match:
            if match.groups()[0] == 'Yes':
                self.musical_background = True
            else:
                self.musical_background = False
        else:
            raise EIMParsingError("Invalid musical background line: %s:%d"
                    % (self._filepath, number))

    def parse_nationality_line(self, line, number):
        """
        Parses the 'Nationality' line from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_nationality_line('"02_Nationality" , symbol United States ;', 1)
        >>> p.nationality
        'United States'

        >>> p.parse_nationality_line('"02_Nationality" , symbol USA ;', 1)
        >>> p.nationality
        'USA'

        >>> p.parse_nationality_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid nationality line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search('symbol ([a-zA-Z_ ]+) ;', line)
        if match:
            self.nationality = match.groups()[0]
        else:
            raise EIMParsingError("Invalid nationality line: %s:%d"
                    % (self._filepath, number))

    def parse_dob_line(self, line, number):
        """
        Parses the 'DOB' line from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_dob_line('"01b_DOB" , 1979 ;', 1)
        >>> p.dob
        1979

        >>> p.parse_dob_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid DOB line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search('(\d{4})', line)
        if match:
            self.dob = int(match.groups()[0])
        else:
            raise EIMParsingError("Invalid DOB line: %s:%d"
                    % (self._filepath, number))

    def parse_sex_line(self, line, number):
        """
        Parses the 'Sex' line from an answer file.

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_sex_line('"01a_Sex" , symbol Male ;', 1)
        >>> p.sex
        'Male'

        >>> p = EIMAnswersParser('./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt')
        >>> p.parse_sex_line('"01a_Sex" , symbol Female ;', 1)
        >>> p.sex
        'Female'

        >>> p.parse_sex_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError: Invalid sex line: ./data/MANILA/SERVER/2012-12-20/ManilaTerminal/T2/20-12-2012/experiment/T2_S0448_answers.txt:1
        """
        match = re.search('(Male|Female)', line)
        if match:
            self.sex = match.groups()[0]
        else:
            raise EIMParsingError("Invalid sex line: %s:%d"
                    % (self._filepath, number))

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
