#!/usr/local/bin/python3

# https://python-plexapi.readthedocs.io/en/latest/modules/media.html
# https://github.com/liamks/libpytunes/blob/master/README.md

from datetime import datetime
import time
from configparser import ConfigParser
from os import path

from plexapi.myplex import MyPlexAccount
from libpytunes import Library

CURRENT_DATE = datetime.now() # time.localtime()
OLDEST_DATE = datetime(1996, 1 , 1) #time.localtime(820450800)

CURRENT_YEAR = datetime.now().year
OLDEST_TRACK_YEAR = 1850

configuration = ConfigParser()
configuration.read("itunes_plex.cfg")

plexUrl = configuration.get('Plex', 'plexUrl')
plexName = configuration.get('Plex', 'plexName')
plexToken = configuration.get('Plex', 'plexToken')
# plexAccount = configuration.get('Plex', 'plexAccount')
#plexPassword = configuration.get('Plex', 'plexPassword')
#plexIdentifier = configuration.get('Plex', 'plexIdentifier')

itunesLibraryPath = configuration.get('iTunes', 'itunesLibraryPath')

def validatePlexTrack(plex_track):
    assert plex_track.userRating >= 0.0
    assert plex_track.userRating <= 10.0

    if plex_track.year:
        assert plex_track.year > OLDEST_TRACK_YEAR
        assert plex_track.year <= CURRENT_YEAR

    assert plex_track.userRating >= 0.0
    assert plex_track.userRating <= 10.0

    assert plex_track.addedAt <= CURRENT_DATE
    assert plex_track.addedAt > OLDEST_DATE
    # if plex_track.addedAt < OLDEST_DATE:
    #     print("Your date is old: %s" % plex_track.addedAt)

    if plex_track.index:
        assert int(plex_track.index) >= 0
        #assert int(plex_track.index) < 100
        # if int(plex_track.index) > 100:
        #     print ("Oddly large track number: %d" % plex_track.index)

    if plex_track.lastViewedAt is not None:
        assert plex_track.lastViewedAt <= CURRENT_DATE
        assert plex_track.lastViewedAt > OLDEST_DATE

    # title (str) - Artist, Album or Track title. (Jason Mraz, We Sing, Lucky, etc.)
    # originalTitle (str) - Track artist.
    # titleSort (str) - Title to use when sorting (defaults to title).

    # viewCount (int) - Count of times this item was accessed.
    assert plex_track.viewCount >= 0


class FakePlexTrack:
    originalTitle = ""
    userRating = 0.0
    year = None
    addedAt = CURRENT_DATE
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

def timeTupToDatetime(timetup):
    datetime_output =  datetime(*timetup[:6])
    assert datetime_output < CURRENT_DATE
    assert datetime_output > OLDEST_DATE

    return datetime_output

print("[INFO] Connecting to Plex server...")
account = MyPlexAccount(token=plexToken)
plex = account.resource(plexName).connect()
music = plex.library.section('Music')

print("[INFO] Loading Plex music library in memory. This may take a while...")
plexLibrary = music.searchTracks()
plexLibraryCount = len(plexLibrary)
print("[INFO] Total number of Plex tracks: ", plexLibraryCount)
time.sleep(2)

itunesLibrary = Library(itunesLibraryPath)
itunesLibraryCount = len(itunesLibrary.songs.items())
print("[INFO] Total number of iTunes tracks: ", itunesLibraryCount)
itunesSongs = {}

# Sort itunes songs into dictionary by file path
for _, song in itunesLibrary.songs.items():
    if song.location and song.location.startswith('Volumes/'):
        posixPath = "/%s" % song.location
        itunesSongs[posixPath] = song

del itunesLibrary

print("[INFO] Total number of iTunes track file entries: ", len(itunesSongs))

libraryMisses = 0

for plex_track_real in plexLibrary:
    plex_path = plex_track_real.media[0].parts[0].file
    if not plex_path in itunesSongs:
        # print("'%s' not found in itunesSongs" % plex_path)
        libraryMisses += 1
        continue

    itunesTrack = itunesSongs[plex_path]

    assert path.isfile(plex_path)

    plex_track = FakePlexTrack(plex_track_real)

    validatePlexTrack(plex_track)

    if plex_track.userRating:
        # (float) - Rating of this track (0.0 - 10.0) equaling (0 stars - 5 stars)
        plex_track.userRating = itunesTrack.rating/10.0

    # (int) - Year this track was released.
    plex_track.year = itunesTrack.year

    # addedAt (datetime) - Datetime this item was added to the library.
    plex_track.addedAt = timeTupToDatetime(itunesTrack.date_added)

    # index (sting) - Index Number (often the track number).
    if itunesTrack.track_number:
        plex_track.index = itunesTrack.track_number

    # lastViewedAt (datetime) - Datetime item was last accessed.
    if itunesTrack.lastplayed:
        plex_track.lastViewedAt = timeTupToDatetime(itunesTrack.lastplayed)

    # title (str) - Artist, Album or Track title. (Jason Mraz, We Sing, Lucky, etc.)
    # originalTitle (str) - Track artist.
    # titleSort (str) - Title to use when sorting (defaults to title).

    # viewCount (int) - Count of times this item was accessed.
    if itunesTrack.play_count:
        plex_track.viewCount = itunesTrack.play_count

    validatePlexTrack(plex_track)

print ("libraryMisses=%d" % libraryMisses)
