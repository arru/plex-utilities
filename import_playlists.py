import ImportUtils

CONFIGURATION = ImportUtils.get_configuration()

plex = ImportUtils.PlexWrapper(CONFIGURATION)
MUSIC_SECTION = plex.api.library.section('Music')
plex_tracks = plex.get_tracks_dict()

itunes = ImportUtils.ItunesWrapper(CONFIGURATION)

itunesPlaylists=itunes.library.getPlaylistNames()

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
                assert not 'Varpan' in track_path
        if len(playlist_items) > 0:
            plex.api.playlist.Playlist.create(plex, playlist_content.name, items=playlist_items, MUSIC_SECTION)
