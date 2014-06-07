% Plot song ratings on the Russell circumplex

% Parse JSON data into a MATLAB struct
data = loadjson('song_ratings.json');

figure('Units', 'pixels', 'Position', [100 100 800 700]);
axis([1, 5, 1, 5]);
line([1 5], [3 3]);
line([3 3], [1 5]);
hold on;

% Iterate over struct keys
data_fields = fieldnames(data);
for i = 1:length(data_fields)
    
    this_song = data.(data_fields{i});
    
    % Calculate arousal statistics
    this_song_arousal = mean(this_song.Activity);
    this_song_valence = mean(this_song.Positivity);
    
    plot(this_song_valence, this_song_arousal, 'Marker', 'o');
    label = data_fields{i};
    text(this_song_valence + .05, this_song_arousal, label);
end
