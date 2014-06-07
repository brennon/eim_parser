# This script builds a list of all songs played during the Singapore
# experiment. It saves this list to a JSON file, along with the three-
# dimensional self-report scores from each subject for each song.

import os, re, json

# Helper functions

def get_attribute_for_song_index(attribute, index, filename):

    attribute_value = None

    # Compile regex
    regex = re.compile(".*Song%d_.*_%s.*(\d) ;" % (index, attribute))

    try:
        file = open(filename)

        for line in file:
            line_match = regex.match(line)

            if line_match:
                attribute_value = int(line_match.group(1))
                break

    except:
        print('Could not read from file: %s' % filename)
        if file:
            file.close()

    return attribute_value

# Main script

# Change this to the correct directory
base_directory = '/Users/brennon/Downloads/SINGAPORE'

# Container for all info files
info_files = list()

# Container for all answer files
answer_files = list()

# Iterate over all subdirectories
for (dirpath, dirnames, filenames) in os.walk(base_directory):

    # Iterate over all files
    for filename in filenames:

        # Regexes for filetypes
        info_match = re.match(".*1nfo.txt$", filename)
        answer_match = re.match(".*answers.txt$", filename)

        # Add to info_files if this is an info file
        if info_match:
            info_files.append(os.path.join(dirpath, filename))

        # Add to answer_files if this is an answer file
        elif answer_match:
            answer_files.append(os.path.join(dirpath, filename))

# Build dictionary for song orders
# {
#     'session1' :
#         [ 'song1', 'song2', song3' ],
#     'session2' : [...],
#     ...
# }
orders = dict()

# Iterate over info files and populate orders dictionary
for filename in info_files:

    # Get session ID
    filename_match = re.match(".*(S\d{4}).*", filename)
    session_id = filename_match.group(1)

    # Add a top-level entry to the dictionary
    orders[session_id] = list()

    # Parse song names from file
    try:
        file = open(filename)

        song_names = None
        for line in file:
            song_line_match = \
                re.match(".*(.\d{3}).wav-(.\d{3}).wav-(.\d{3}).wav.*", line)

            if song_line_match:
                for song in song_line_match.groups():
                    orders[session_id].append(song)
                break

    except:
        print('Could not read from file: %s' % filename)
        if file:
            file.close()

# Build dictionary for song ratings
# {
#     'song1' :
#         {
#             'arousal' : 4,
#             'valence' : 3,
#             'dominance' : 1
#         },
#     'song2' : {...},
#     ...
# }
ratings = dict()

# Iterate over answer files
for filename in answer_files:

    # Get session ID
    filename_match = re.match(".*(S\d{4}).*", filename)
    session_id = filename_match.group(1)

    # Get song labels
    song_labels = orders[session_id]

    # Ensure that each song is in ratings dictionary
    for label in song_labels:
        if label not in ratings.keys():
            ratings[label] = dict()
            ratings[label]['Positivity'] = list()
            ratings[label]['Activity'] = list()
            ratings[label]['Power'] = list()

    # Iterate over each song
    for song_index in [1,2,3]:

        # Get specific song label
        song_label = song_labels[song_index - 1]

        # Get attribute-specific ratings
        for attribute in ['Positivity', 'Activity', 'Power']:

            rating = get_attribute_for_song_index(attribute, song_index, filename)
            ratings[song_label][attribute].append(rating)

# Write dictionary to file
output_file = open('song_ratings.json', 'w')
json.dump(ratings, output_file)

print('Info files: %d' % len(info_files))
print('Answer files: %d' % len(answer_files))
