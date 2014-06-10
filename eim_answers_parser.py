from eim_parser import EIMParser, EIMParsingError
import re, datetime, sys, os

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
        self.temporary_ratings = None
        self.ratings = None
        self.most_enjoyed = None
        self.most_engaged = None
        self.emotion_indices = None
        self.temporary_emotion_indices = None
        self.music_styles = list()
        self.version = None

        self.determine_file_version()

    def determine_file_version(self):
        """
        Determines the file version from among the four Dublin versions and the
        one version used everywhere else.

        >>> p = EIMAnswersParser('./test_data/DUBLIN/MuSE_SERVER/06-Jul-2010/T4_S0106_answers.txt')
        >>> p.determine_file_version()
        >>> p.version
        1

        >>> p = EIMAnswersParser('./test_data/DUBLIN/MuSE_SERVER/20-Aug-2010/T4_S0770_answers.txt')
        >>> p.determine_file_version()
        >>> p.version
        2

        >>> p = EIMAnswersParser('./test_data/DUBLIN/MuSE_SERVER/05-Sep-2010/T3_S1016_answers.txt')
        >>> p.determine_file_version()
        >>> p.version
        3

        >>> p = EIMAnswersParser('./test_data/DUBLIN/MuSE_SERVER/30-Sep-2010/T3_S1266_answers.txt')
        >>> p.determine_file_version()
        >>> p.version
        4

        >>> p = EIMAnswersParser('./test_data/NYC/SERVER_NYC/2011-07-07/terminals/T2/2011-07-07/T2_S0342_answers.txt')
        >>> p.determine_file_version()
        >>> p.version
        5
        """
        dublin_a = (datetime.datetime(2010,7,1),datetime.datetime(2010,7,21,23,59))
        dublin_b = (datetime.datetime(2010,7,23),datetime.datetime(2010,8,29,23,59))
        dublin_c = (datetime.datetime(2010,8,31),datetime.datetime(2010,9,19,23,59))
        dublin_d = (datetime.datetime(2010,9,21),datetime.datetime(2010,10,1,23,59))

        filetime = datetime.datetime.fromtimestamp(os.stat(self._filepath).st_mtime)

        if filetime >= dublin_a[0] and filetime <= dublin_a[1]:
            self.version = 1
            return
        elif filetime >= dublin_b[0] and filetime <= dublin_b[1]:
            self.version = 2
            return
        elif filetime >= dublin_c[0] and filetime <= dublin_c[1]:
            self.version = 3
            return
        elif filetime >= dublin_d[0] and filetime <= dublin_d[1]:
            self.version = 4
            return
        elif filetime >= dublin_d[1]:
            self.version = 5
            return

        raise EIMParsingError('Could not determine answer file version: %s' % self._filepath)

    def to_dict(self):
        """
        Assembles a dictionary of parsed data.

        >>> p = EIMAnswersParser('./test_data/BERGEN/SERVER/2012-02-01/BergenTerminal/02-02-2012/experiment/T0_S0822_answers.txt')
        >>> p.parse()
        >>> out_dict = p.to_dict()['answers']
        >>> out_dict['sex']
        'female'
        >>> out_dict['dob']
        1954
        >>> out_dict['nationality']
        'norwegian'
        >>> out_dict['musical_background']
        False
        >>> out_dict['musical_expertise']
        4
        >>> out_dict['hearing_impairments']
        False
        >>> out_dict['visual_impairments']
        False
		>>> out_dict['ratings']['engagement'][0]
		5
		>>> out_dict['ratings']['positivity'][0]
		5
		>>> out_dict['ratings']['activity'][0]
		4
		>>> out_dict['ratings']['power'][0]
		5
		>>> out_dict['ratings']['chills'][0]
		1
		>>> out_dict['ratings']['like_dislike'][0]
		4
		>>> out_dict['ratings']['familiarity'][0]
		4
		>>> out_dict['ratings']['engagement'][1]
		4
		>>> out_dict['ratings']['positivity'][1]
		5
		>>> out_dict['ratings']['activity'][1]
		4
		>>> out_dict['ratings']['power'][1]
		5
		>>> out_dict['ratings']['chills'][1]
		1
		>>> out_dict['ratings']['like_dislike'][1]
		4
		>>> out_dict['ratings']['familiarity'][1]
		3
		>>> out_dict['ratings']['engagement'][2]
		5
		>>> out_dict['ratings']['positivity'][2]
		5
		>>> out_dict['ratings']['activity'][2]
		3
		>>> out_dict['ratings']['power'][2]
		5
		>>> out_dict['ratings']['chills'][2]
		1
		>>> out_dict['ratings']['like_dislike'][2]
		5
		>>> out_dict['ratings']['familiarity'][2]
		4
        >>> out_dict['most_engaged']
        3
        >>> out_dict['most_enjoyed']
        1
        >>> out_dict['music_styles']
        ['classical', 'jazz', 'world']
        >>> out_dict['emotion_indices']
        [31.799, 17.038, 8.08558]
        >>> p.to_dict()['metadata']['session_number']
        822
        >>> p.to_dict()['metadata']['terminal']
        0
        >>> p.to_dict()['metadata']['location']
        'bergen'
        """
        answers_dict = {
            'metadata': self._experiment_metadata,
            'answers':{
                'sex':self.sex,
                'dob':self.dob,
                'nationality':self.nationality,
                'musical_background':self.musical_background,
                'musical_expertise':self.musical_expertise,
                'hearing_impairments':self.hearing_impairments,
                'visual_impairments':self.visual_impairments,
                'most_engaged':self.most_engaged,
                'most_enjoyed':self.most_enjoyed,
                'music_styles':self.music_styles,
                'emotion_indices':self.emotion_indices,
                'ratings':self.ratings
            }
        }

        return answers_dict

    def parse(self):
        """
        Parses correct number of lines in a file according to answer file
        version.

        >>> p = EIMAnswersParser('./test_data/DUBLIN/MuSE_SERVER/05-Sep-2010/T1_S0942_answers.txt')
        >>> p.parse()
        >>> json = p.to_dict()
        >>> json['answers']['sex']
        'male'
        >>> json['answers']['ratings']['wonder'][2]
        3

        >>> p = EIMAnswersParser('./test_data/DUBLIN/MuSE_SERVER/14-Aug-2010/T3_S0739_answers.txt')
        >>> p.parse()
        >>> json = p.to_dict()
        >>> len(json['answers']['ratings']['engagement'])
        3
        >>> json['answers']['music_styles']
        ['rock', 'pop', 'traditional_irish']
        """
        allowed_lines = 0

        if self.version == 1:
            allowed_lines = 84
        elif self.version == 2:
            allowed_lines = 41
        elif self.version == 3:
            allowed_lines = 47
        elif self.version == 4:
            allowed_lines = 20

        try:
            self.open_file()
            lines = list(self._file)

            total_lines = len(lines)

            if self.version == 5:
                start_line = 0
            else:
                start_line = total_lines - allowed_lines


            # If a date line is present, parse it first
            for number, line in enumerate(lines):
                if number >= start_line:
                    if re.search('DATE', line):
                        try:
                            self.parse_line(line, number + 1)
                        except:
                            self.logger.error(e)
                        break

            # Parse all allowed lines
            for number, line in enumerate(lines):
                if number >= start_line:
                    try:
                        self.parse_line(line, number + 1)
                    except Exception as e:
                        self.logger.error(e)

            # Parse session id
            match = re.search('T\d_S(\d{4})_.*.txt', self._filepath)
            if match:
                self._experiment_metadata['session_number'] = int(match.groups()[0])
            else:
                raise EIMParsingError("No valid session id found in filename %s" % self._filepath)

        except:
            raise

        finally:
            if self._file and not self._file.closed:
                self.close_file()

    def parse_line(self, line, number):
        """
        Parses a line of text from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_line('"01a_Sex , symbol Female ;', 1)
        >>> p.sex
        'female'

        >>> p.parse_line('"01b_DOB" , 1983 ;', 2)
        >>> p.dob
        1983

        >>> p.parse_line('"02_Nationality" , symbol Filipino ;', 3)
        >>> p.nationality
        'filipino'

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
        >>> p.ratings['engagement'][0]
        3

        >>> p.parse_line('"Song1_Scale2_Positivity" , 3 ;', 9)
        >>> p.ratings['positivity'][0]
        3

        >>> p.parse_line('"Song1_Scale3_Activity" , 2 ;', 10)
        >>> p.ratings['activity'][0]
        2

        >>> p.parse_line('"Song1_Scale4_Power" , 3 ;', 11)
        >>> p.ratings['power'][0]
        3

        >>> p.parse_line('"Song1_Scale5_Chills" , 1 ;', 12)
        >>> p.ratings['chills'][0]
        1

        >>> p.parse_line('"Song1_Scale6_like_dislike" , 2 ;', 13)
        >>> p.ratings['like_dislike'][0]
        2

        >>> p.parse_line('"Song1_Scale7_Familiarity" , 4 ;', 14)
        >>> p.ratings['familiarity'][0]
        4

        >>> p.parse_line('"Song2_Scale1_Engagement" , 1 ;', 15)
        >>> p.ratings['engagement'][1]
        1

        >>> p.parse_line('"Song2_Scale2_Positivity" , 2 ;', 16)
        >>> p.ratings['positivity'][1]
        2

        >>> p.parse_line('"Song2_Scale3_Activity" , 1 ;', 17)
        >>> p.ratings['activity'][1]
        1

        >>> p.parse_line('"Song2_Scale4_Power" , 3 ;', 18)
        >>> p.ratings['power'][1]
        3

        >>> p.parse_line('"Song2_Scale5_Chills" , 1 ;', 19)
        >>> p.ratings['chills'][1]
        1

        >>> p.parse_line('"Song2_Scale6_like_dislike" , 1 ;', 20)
        >>> p.ratings['like_dislike'][1]
        1

        >>> p.parse_line('"Song2_Scale7_Familiarity" , 1 ;', 21)
        >>> p.ratings['familiarity'][1]
        1

        >>> p.parse_line('"Song3_Scale1_Engagement" , 2 ;', 22)
        >>> p.ratings['engagement'][2]
        2

        >>> p.parse_line('"Song3_Scale2_Positivity" , 3 ;', 23)
        >>> p.ratings['positivity'][2]
        3

        >>> p.parse_line('"Song3_Scale3_Activity" , 2 ;', 24)
        >>> p.ratings['activity'][2]
        2

        >>> p.parse_line('"Song3_Scale4_Power" , 3 ;', 25)
        >>> p.ratings['power'][2]
        3

        >>> p.parse_line('"Song3_Scale5_Chills" , 1 ;', 26)
        >>> p.ratings['chills'][2]
        1

        >>> p.parse_line('"Song3_Scale6_like_dislike" , 2 ;', 27)
        >>> p.ratings['like_dislike'][2]
        2

        >>> p.parse_line('"Song3_Scale7_Familiarity" , 1 ;', 28)
        >>> p.ratings['familiarity'][2]
        1

        >>> p.parse_line('FinalQ_Most_Engaged , 1 ;', 29)
        >>> p.most_engaged
        1

        >>> p.parse_line('FinalQ_Most_Enjoyed , 1 ;', 30)
        >>> p.most_enjoyed
        1

        >>> p.parse_line('"EmotionIndex3" , 0.598997 ;', 31)
        >>> p.emotion_indices[2]
        0.598997

        >>> p.parse_line('"EmotionIndex2" , 0.595210 ;', 32)
        >>> p.emotion_indices[1]
        0.59521

        >>> p.parse_line('"EmotionIndex1" , 21.4085 ;', 33)
        >>> p.emotion_indices[0]
        21.4085

        >>> p.parse_line('"05_Music_Style_None" , 0 ;', 34)
        >>> p.music_styles
        []

        >>> p.parse_line('"05_Music_Style_Pop" , 1 ;', 35)
        >>> p.music_styles
        ['pop']

        >>> p.parse_line('"05_Music_Style_Jazz" , 1 ;', 36)
        >>> p.music_styles
        ['pop', 'jazz']

        >>> p.parse_line('"05_Music_Style_Dance" , 1 ;', 37)
        >>> p.music_styles
        ['pop', 'jazz', 'dance']

        >>> p.parse_line('"05_Music_Style_Hip_Hop" , 1 ;', 38)
        >>> p.music_styles
        ['pop', 'jazz', 'dance', 'hip_hop']

        >>> p.parse_line('SOME CRAZY LINE', 98) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
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

        elif re.search('SONG\d+_', line.upper()):
            self.parse_song_scale_line(line, number)

        elif re.search('FINALQ_MOST', line.upper()):
            self.parse_most_enjoyed_engaged_line(line, number)

        elif re.search('EMOTIONINDEX', line.upper()):
            self.parse_emotion_index_line(line, number)

        elif re.search('MUSIC_?STYLE', line.upper()):
            self.parse_music_style_line(line, number)

        elif re.search('SONG\s?\d [HRST]\d{3}', line.upper()):
            return

        elif re.search('^SONG\d$', line.upper()):
            return

        else:
            raise EIMParsingError('Unprocessed line: %s:%d %s' % (self._filepath, number, line))

    def parse_most_enjoyed_engaged_line(self, line, number):
        """
        Parses the 'Most Enjoyed / Engaged' lines from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_most_enjoyed_engaged_line('FinalQ_Most_Enjoyed , 3 ;', 1)
        >>> p.most_enjoyed
        3

        >>> p.parse_most_enjoyed_engaged_line('FinalQ_Most_Engaged , 4 ;', 1)
        >>> p.most_engaged
        4

        >>> p.parse_most_enjoyed_engaged_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        match = re.search('FinalQ_Most_(\w+)[\s,]+(\d+)', line)
        empty_match = re.search('^FinalQ_Most_(\w+)$', line)

        if match:
            if match.groups()[0] in ['Enjoyed', 'Ejoyed']:
                self.most_enjoyed = int(match.groups()[1])
            elif match.groups()[0] == 'Engaged':
                self.most_engaged = int(match.groups()[1])
        elif empty_match:
            return
        else:
            raise EIMParsingError("Invalid most enjoyed / engaged line: %s:%d"
                    % (self._filepath, number))

    def parse_musical_expertise_line(self, line, number):
        """
        Parses the 'Musical Expertise' line from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_musical_expertise_line('"03_Musical_Expertise" , 3 ;', 1)
        >>> p.musical_expertise
        3

        >>> p.parse_musical_expertise_line('"03_Musical_Expertise" , symbol Lots ;', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        match = re.search('Musical_Expertise.*(\d+)', line)
        empty_match = re.search('Musical_Expertise$', line)
        if match:
            self.musical_expertise = int(match.groups()[0])
        elif empty_match:
            return
        else:
            raise EIMParsingError("Invalid musical expertise line: %s:%d"
                    % (self._filepath, number))

    def parse_music_style_line(self, line, number):
        """
        Parses an 'Music Style' line from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_music_style_line('"05_Music_Style_Pop" , 1 ;', 1)
        >>> p.music_styles
        ['pop']

        >>> p.parse_music_style_line('"05_Music_Style_None" , 0 ;', 1)
        >>> p.music_styles
        ['pop']

        >>> p.music_styles = None
        >>> p.parse_music_style_line('"05_Music_Style_None" , 1 ;', 1)
        >>> p.music_styles
        ['none']

        >>> p.parse_music_style_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        """
        match_dublin = re.search('^\"?\d+_Music_Style_(\w+)$', line)
        match_others = re.search('^\"?\d+_Music_Style_(\w+)[\",\s]+(\d+)[\s;]+$', line)

        style = None
        value = None

        if match_dublin:
            style = match_dublin.groups()[0].lower()
            value = 1
        elif match_others:
            style = match_others.groups()[0].lower()
            value = int(match_others.groups()[1])

        if style:
            if value:
                if not self.music_styles:
                    self.music_styles = list()
                self.music_styles.append(style)
        """

        match = re.search('\"?05_Music_Style_(\w+)\"?[\s,]+1', line)
        match_empty = re.search('Music_Style_(\w+)$', line)
        match_zero = re.search('\"?05_Music_Style_(\w+)\"?[\s,]+0', line)

        if match:
            if not self.music_styles:
                self.music_styles = list()
            self.music_styles.append(match.groups()[0].lower())

        else:
            if match_empty or match_zero:
                return
            raise EIMParsingError("Invalid music style line: %s:%d"
                    % (self._filepath, number))

    def sort_emotion_indices(self):
        """
        Sorts temporary emotion indices into index array

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.temporary_emotion_indices = []
        >>> p.sort_emotion_indices()

        >>> p.temporary_emotion_indices.append({'index':8,'value':2})
        >>> p.sort_emotion_indices()
        >>> p.emotion_indices[7]
        2.0

        >>> p.temporary_emotion_indices.append({'index':3,'value':1})
        >>> p.sort_emotion_indices()
        >>> p.temporary_emotion_indices.append({'index':94,'value':8})
        >>> p.sort_emotion_indices()
        >>> p.emotion_indices[93]
        8.0
        >>> p.emotion_indices[2]
        1.0
        >>> p.emotion_indices[7]
        2.0

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        # Iterate over temporary list
        max_index = 0
        for entry in self.temporary_emotion_indices:
            if entry['index'] > max_index:
                max_index = entry['index']

        self.emotion_indices = [None for x in range(max_index)]

        for entry in self.temporary_emotion_indices:
            self.emotion_indices[int(entry['index'] - 1)] = float(entry['value'])

    def parse_emotion_index_line(self, line, number):
        """
        Parses an 'Emotion Index' line from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_emotion_index_line('"EmotionIndex2" , 36.4641 ;', 1)
        >>> p.emotion_indices[1]
        36.4641
        >>> p.parse_emotion_index_line('"EmotionIndex84" , 18.5 ;', 1)
        >>> p.emotion_indices[83]
        18.5
        >>> p.parse_emotion_index_line('"EmotionIndex1" , 1.0 ;', 1)
        >>> p.emotion_indices[0]
        1.0

        >>> p.parse_emotion_index_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        match = re.search('"EmotionIndex(\w+)" , (\d+\.\d+) ;', line)
        if match:
            if not self.temporary_emotion_indices:
                self.temporary_emotion_indices = list()
            number = match.groups()[0]
            value = float(match.groups()[1])
            self.temporary_emotion_indices.append({'index':int(number),'value':value})
            self.sort_emotion_indices()
        else:
            raise EIMParsingError("Invalid emotion index line: %s:%d"
                    % (self._filepath, number))

    def sort_ratings(self):
        """
        Sorts temporary song ratings into ratings arrays

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.sort_ratings()

        >>> p.temporary_ratings = {'power':None}
        >>> p.sort_ratings()

        >>> p.temporary_ratings['power'] = [{'index':3,'value':3},{'index':1,'value':4}]
        >>> p.sort_ratings()
        >>> p.ratings['power'][0]
        4
        >>> p.ratings['power'][1]

        >>> p.ratings['power'][2]
        3
        >>> p.temporary_ratings['power'].append({'index':2,'value':1})
        >>> p.sort_ratings()
        >>> p.ratings['power'][0]
        4
        >>> p.ratings['power'][1]
        1
        >>> p.ratings['power'][2]
        3

        >>> p.temporary_ratings['power'].append({'index':5,'value':1})
        >>> p.sort_ratings()
        >>> p.ratings['power'][4]
        1

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        # Bail if there are not yet any ratings
        if not self.temporary_ratings:
            return

        if not self.ratings:
            self.ratings = dict()

        # Iterate over temporary ratings keys
        for scale in self.temporary_ratings.keys():

            # Bail if there are no ratings for this key
            if not self.temporary_ratings[scale]:
                continue

            max_index = 0

            # Iterate over list of dicts to find max index
            for entry in self.temporary_ratings[scale]:

                if entry['index'] > max_index:
                    max_index = entry['index']

            # Set main ratings list for this scale to a list of the correct size
            self.ratings[scale] = [None for x in range(max_index)]

            # Load list with entry values
            for entry in self.temporary_ratings[scale]:

                self.ratings[scale][entry['index'] - 1] = entry['value']

    def parse_song_scale_line(self, line, number):
        """
        Parses a 'Song Scale' line from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_song_scale_line('"Song2_Scale4_Power" , 5 ;', 1)
        >>> p.ratings['power'][1]
        5
        >>> p.ratings['power'][0]

        >>> p.parse_song_scale_line('"Song1_Scale4_Power" , 3 ;', 1)
        >>> p.ratings['power'][0]
        3

        >>> p.parse_song_scale_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        # Create dictionaries if they don't yet exist
        if not self.ratings:
            self.ratings = dict()

        if not self.temporary_ratings:
            self.temporary_ratings = dict()

        match = re.search('Song(\d+)_(?:Scale\d+[a-z]?_)?(\w+).*(\d)', line)
        empty_match = re.search('Song(\d+)_(?:Scale\d+_)?(\w+)$', line)
        if match:
            number = int(match.groups()[0])
            scale = match.groups()[1].lower()
            value = int(match.groups()[2])
            if scale not in self.temporary_ratings:
                self.temporary_ratings[scale] = list()
            self.temporary_ratings[scale].append({'index':number,'value':value})
        elif empty_match:
            number = int(match.groups()[0])
            scale = match.groups()[1].lower()
            if scale not in self.temporary_ratings:
                self.temporary_ratings[scale] = list()
            self.temporary_ratings[scale].append({'index':number,'value':None})
        else:
            raise EIMParsingError("Invalid song scale line: %s:%d"
                    % (self._filepath, number))

        # Re-sort the song ratings
        self.sort_ratings()

    def parse_visual_impairments_line(self, line, number):
        """
        Parses the 'Hearing Impairments' line from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_visual_impairments_line('"04_Visual_Impairments" , symbol Yes ;', 1)
        >>> p.visual_impairments
        True

        >>> p.parse_visual_impairments_line('"04_Visual_Impairments" , symbol No ;', 1)
        >>> p.visual_impairments
        False

        >>> p.parse_visual_impairments_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        match = re.search('(Yes|No)', line)
        empty_match = re.search('Impairments$', line)
        if match:
            if match.groups()[0] == 'Yes':
                self.visual_impairments = True
            else:
                self.visual_impairments = False
        elif empty_match:
            return
        else:
            raise EIMParsingError("Invalid visual impairments line: %s:%d"
                    % (self._filepath, number))

    def parse_hearing_impairments_line(self, line, number):
        """
        Parses the 'Hearing Impairments' line from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_hearing_impairments_line('"04_Hearing_Impairments" , symbol Yes ;', 1)
        >>> p.hearing_impairments
        True

        >>> p.parse_hearing_impairments_line('"04_Hearing_Impairments" , symbol No ;', 1)
        >>> p.hearing_impairments
        False

        >>> p.parse_hearing_impairments_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        match = re.search('(Yes|No)', line)
        empty_match = re.search('Impairments$', line)
        if match:
            if match.groups()[0] == 'Yes':
                self.hearing_impairments = True
            else:
                self.hearing_impairments = False
        elif empty_match:
            return
        else:
            raise EIMParsingError("Invalid hearing impairments line: %s:%d"
                    % (self._filepath, number))

    def parse_musical_background_line(self, line, number):
        """
        Parses the 'Musical Background' line from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_musical_background_line('"03_Musical_Background" , symbol Yes ;', 1)
        >>> p.musical_background
        True

        >>> p.parse_musical_background_line('"03_Musical_Background" , symbol No ;', 1)
        >>> p.musical_background
        False

        >>> p.parse_musical_background_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        empty = re.search('^03_Musical_Background$', line)
        if empty:
            self.musical_background = None
        else:
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

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_nationality_line('"02_Nationality" , symbol United States ;', 1)
        >>> p.nationality
        'united states'

        >>> p.parse_nationality_line('"02_Nationality" , symbol USA ;', 1)
        >>> p.nationality
        'usa'

        >>> p.parse_nationality_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        match = re.search('\"?02_Nationality\"?[,\s]+(?:symbol )?([\s\w]+)', line)
        empty_match = re.search('Nationality$', line)
        if match:
            self.nationality = match.groups()[0].lower().strip()
        elif empty_match:
            return
        else:
            raise EIMParsingError("Invalid nationality line: %s:%d"
                    % (self._filepath, number))

    def parse_dob_line(self, line, number):
        """
        Parses the 'DOB' line from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_dob_line('"01b_DOB" , 1979 ;', 1)
        >>> p.dob
        1979

        >>> p.parse_dob_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        match = re.search('DOB[\",\s]+(\d{1,4})', line)
        empty_match = re.search('DOB$', line)
        if match:
            year = int(match.groups()[0])
            if year == 0:
                year = None
            self.dob = year
        elif empty_match:
            return
        else:
            raise EIMParsingError("Invalid DOB line: %s:%d"
                    % (self._filepath, number))

    def parse_sex_line(self, line, number):
        """
        Parses the 'Sex' line from an answer file.

        >>> f = open('./test_data/.SINGAPORE_T2_S0448_answers.txt', 'w')
        >>> f.close()

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_sex_line('"01a_Sex" , symbol Male ;', 1)
        >>> p.sex
        'male'

        >>> p = EIMAnswersParser('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        >>> p.parse_sex_line('"01a_Sex" , symbol Female ;', 1)
        >>> p.sex
        'female'

        >>> p.parse_sex_line('BAD LINE', 1) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        eim_parser.EIMParsingError:

        >>> import os
        >>> os.unlink('./test_data/.SINGAPORE_T2_S0448_answers.txt')
        """
        match = re.search('(Male|Female)', line)
        empty_match = re.search('Sex$', line)
        if match:
            self.sex = match.groups()[0].lower()
        elif empty_match:
            return
        else:
            raise EIMParsingError("Invalid sex line: %s:%d"
                    % (self._filepath, number))

def __test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    __test()
