import ImportUtils
import plexapi.playlist

# Audio codecs in ascending order of preference (best goes last)
CODEC_RATING = [
'mp2',
'mp3',
'aac',
'pcm',
'wav',
'aiff',
'alac',
'flac'
]

CONFIGURATION = ImportUtils.get_configuration()

# Duration match tolerance in ms
duration_fuzziness = 2500

plex = ImportUtils.PlexWrapper(CONFIGURATION)
MUSIC_SECTION = plex.server.library.section('Music')
plex_tracks = MUSIC_SECTION.searchTracks()

print ("[INFO] clustering %d tracks" % len(plex_tracks))
print ("[INFO] using %dms fuzziness" % duration_fuzziness)

track_clusters = {}

for plex_track in plex_tracks:
    #grandparentRatingKey (str) – Unique key identifying album artist.
    # media.bitrate
    if not plex_track.title or not plex_track.artist():
        continue

    key = (plex_track.title, plex_track.artist(), int(plex_track.media[0].duration/duration_fuzziness))
    if key in track_clusters:
        track_clusters[key].append (plex_track)
    else:
        track_clusters[key] = [plex_track]

uniques_counter = 0
duplicate_groups_counter = 0

print ("[INFO] finding highest bitrate in %d clusters" % len(track_clusters))

duplicate_playlist_items = []

for key, cluster in track_clusters.items():
    if len(cluster) > 1:
        highest_bitrate_value = 0
        highest_bitrate_codec_index = 0
        highest_bitrate_track = None
        for track in cluster:
            codec = track.media[0].audioCodec.lower()
            codec_index = CODEC_RATING.index(codec)
            if codec_index > highest_bitrate_codec_index or (codec_index >= highest_bitrate_codec_index and track.media[0].bitrate > highest_bitrate_value):
                highest_bitrate_value = track.media[0].bitrate
                highest_bitrate_track = track
                highest_bitrate_codec_index = codec_index

        lower_bitrate_duplicates = filter(lambda t: t is not highest_bitrate_track, cluster)
        duplicate_playlist_items.extend(lower_bitrate_duplicates)

        # print ("Duplicate: %s\t(%d kbps)" % (str(key), highest_bitrate_track.media[0].bitrate))

        duplicate_groups_counter += 1
    else:
        uniques_counter += 1

playlist_title = "Duplicates (lower bitrates)"
try:
    duplicates_playlist = plex.server.playlist(playlist_title)
    duplicates_playlist.delete()
except plexapi.exceptions.NotFound:
    pass

plexapi.playlist.Playlist.create(plex.server, playlist_title, items=duplicate_playlist_items, section=MUSIC_SECTION)

print ("[INFO] %d duplicate songs (%d total redundant tracks) identified" % (duplicate_groups_counter, len(duplicate_playlist_items)))
print ("[INFO] %d singular/unique tracks" % uniques_counter)
