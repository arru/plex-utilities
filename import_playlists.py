import ImportUtils
import plexapi.playlist

CONFIGURATION = ImportUtils.get_configuration()

plex = ImportUtils.PlexWrapper(CONFIGURATION)
MUSIC_SECTION = plex.api.library.section('Music')
plex_tracks = plex.get_tracks_dict()

itunes = ImportUtils.ItunesWrapper(CONFIGURATION)

itunesPlaylists=itunes.library.getPlaylistNames()

print("[INFO] Getting ready to import %d iTunes playlists" % len(itunesPlaylists))

nonempty_playlists_counter = 0
not_found_set = set()

for playlist in itunesPlaylists:
    playlist_content = itunes.library.getPlaylist(playlist)
    # name (String)
    # tracks (List[Song])
    # is_folder = False (Boolean)
    # playlist_persistent_id = None (String)
    # parent_persistent_id = None (String)

    if playlist_content.is_folder:
        print("Skipping playlist folder %s" % playlist_content.name)
    elif len(playlist_content.tracks) == 0:
        print("Skipping empty playlist %s" % playlist_content.name)
    else:
        playlist_items = []
        for track in playlist_content.tracks:
            if not ImportUtils.is_song_on_disk(track):
                continue

            track_path = ImportUtils.normalizeTrackPath(track.location)

            if track_path in plex_tracks:
                playlist_items.append (plex_tracks[track_path])
            else:
                not_found_set.add(track_path)

        if len(playlist_items) > 0:
            plexapi.playlist.Playlist.create(plex.api, playlist_content.name, items=playlist_items, section=MUSIC_SECTION)

            print ("%s\t(%d)\timported" % (playlist_content.name, len(playlist_items)))

            nonempty_playlists_counter += 1

print ("Tracks not found: %d" % len(not_found_set))
