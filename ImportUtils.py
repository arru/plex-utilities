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

def get_configuration():
    configuration = ConfigParser()
    configuration.read("itunes_plex.cfg")

    return configuration

class PlexWrapper():
    api = None

    def __init__(self, configuration):
        plexUrl = configuration.get('Plex', 'plexUrl')
        plexName = configuration.get('Plex', 'plexName')
        plexToken = configuration.get('Plex', 'plexToken')

        print("[INFO] Connecting to Plex server...")
        account = MyPlexAccount(token=plexToken)
        self.api = account.resource(plexName).connect()

    def get_tracks_dict(self):
        """Return all Plex tracks in a dictionary keyed on file path."""

        music = self.api.library.section('Music')

        print("[INFO] Loading Plex music library in memory. This may take a while...")
        plexLibrary = music.searchTracks()
        plexLibraryCount = len(plexLibrary)
        print("[INFO] Total number of Plex tracks: ", plexLibraryCount)
        #time.sleep(2)

        plexTracks = {}

        for track in plexLibrary:
            plexTracks[track.media[0].parts[0].file] = track

        #del plexLibrary

        return plexTracks


class ItunesWrapper():
    library = None

    def __init__(self, configuration):
        itunesLibraryPath = configuration.get('iTunes', 'itunesLibraryPath')

        self.library = Library(itunesLibraryPath)
        itunesLibraryCount = len(self.library.songs.items())
        print("[INFO] Total number of iTunes tracks: ", itunesLibraryCount)

    def get_tracks_dict(self):
        """Return all file-based iTunes tracks in a dictionary keyed on file path."""
        itunesSongs = {}

        # Sort itunes songs into dictionary by file path
        for _, song in self.library.songs.items():
            if song.location and song.location.startswith('Volumes/'):
                posixPath = "/%s" % song.location
                itunesSongs[posixPath] = song

        #del itunesLibrary

        print("[INFO] Total number of iTunes track file entries: ", len(itunesSongs))

        return itunesSongs


def timeTupToDatetime(timetup):
    datetime_output =  datetime(*timetup[:6])
    assert datetime_output < CURRENT_DATE
    assert datetime_output > OLDEST_DATE

    return datetime_output

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
