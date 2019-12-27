#!/usr/local/bin/python3

# https://python-plexapi.readthedocs.io/en/latest/modules/media.html
# https://github.com/liamks/libpytunes/blob/master/README.md

from os import path

import ImportUtils

CONFIGURATION = ImportUtils.get_configuration()

class FakePlexTrack:
    originalTitle = ""
    userRating = 0.0
    year = None
    addedAt = ImportUtils.CURRENT_DATE
    index = 0
    lastViewedAt = None
    title = ""
    titleSort = None
    viewCount = 0

    def __init__(self, plex_track):
        self.originalTitle = plex_track.originalTitle
        self.userRating = plex_track.userRating
        self.year = plex_track.year
        self.addedAt = plex_track.addedAt
        self.index = plex_track.index
        self.lastViewedAt = plex_track.lastViewedAt
        self.title = plex_track.title
        self.titleSort = plex_track.titleSort
        self.viewCount = plex_track.viewCount

plex = ImportUtils.PlexWrapper(CONFIGURATION)
PLEX_TRACKS = plex.server.library.section('Music').searchTracks()

itunes = ImportUtils.ItunesWrapper(CONFIGURATION)
itunes_tracks = itunes.get_tracks_dict()

del itunes

libraryMisses = 0

for plex_track_real in PLEX_TRACKS:
    plex_path = plex_track_real.media[0].parts[0].file

    if not plex_path in itunes_tracks:
        # print("'%s' not found in itunes_tracks" % plex_path)
        libraryMisses += 1
        continue

    itunesTrack = itunes_tracks[plex_path]

    assert path.isfile(plex_path)

    # plex_track = FakePlexTrack(plex_track_real)
    plex_track = plex_track_real

    ImportUtils.validatePlexTrack(plex_track)

    if itunesTrack.rating:
        plex_rating = float(itunesTrack.rating)/10.0
        # (float) - Rating of this track (0.0 - 10.0) equaling (0 stars - 5 stars)
        #.value
        plex_track.edit(**{'userRating.value': plex_rating})

    # (int) - Year this track was released.
    if itunesTrack.year:
        plex_track.edit(**{'year.value': itunesTrack.year})

    # addedAt (datetime) - Datetime this item was added to the library.

    # index (sting) - Index Number (often the track number).
    if itunesTrack.track_number:
        plex_track.edit(**{'index.value': itunesTrack.track_number})

    # lastViewedAt (datetime) - Datetime item was last accessed.
    # title (str) - Artist, Album or Track title. (Jason Mraz, We Sing, Lucky, etc.)
    # originalTitle (str) - Track artist.
    # titleSort (str) - Title to use when sorting (defaults to title).
    # viewCount (int) - Count of times this item was accessed.

    ImportUtils.validatePlexTrack(plex_track)

print ("libraryMisses=%d" % libraryMisses)
