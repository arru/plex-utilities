from datetime import datetime
import time
from configparser import ConfigParser
import os.path
import unicodedata

from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount
from libpytunes import Library

EMPTY_TRACK_TITLES = ['no title', 'untitled', 'unknown', '[unknown]', 'none', '']
EMPTY_ALBUM_TITLES = ['unknown album', '[unknown album]'] + EMPTY_TRACK_TITLES
EMPTY_ARTIST_NAMES = ['unknown artist'] + EMPTY_TRACK_TITLES

CURRENT_DATE = datetime.now() # time.localtime()
OLDEST_DATE = datetime(1996, 1 , 1) #time.localtime(820450800)

CURRENT_YEAR = datetime.now().year
OLDEST_TRACK_YEAR = 1850

def get_configuration():
    configuration = ConfigParser()
    configuration.read("itunes_plex.cfg")

    return configuration
    
def unmarshal_cfg_list(cfg_value):
    return cfg_value.strip().split('\n')

class PlexWrapper():
    server = None

    def __init__(self, configuration):
        plexUrl = configuration.get('Plex', 'plexUrl', fallback=None)
        plexName = configuration.get('Plex', 'plexName')
        plexToken = configuration.get('Plex', 'plexToken')
        
        if plexUrl:
            try:
                print("[INFO] Connecting to local Plex server: %s" % plexUrl)
                self.server = PlexServer(plexUrl, plexToken)
            except:
                print("[INFO] Local connection failed")
                pass
        if not self.server:
            print("[INFO] Connecting through MyPlexAccount")
            account = MyPlexAccount(token=plexToken)
            self.server = account.resource(plexName).connect()

    def get_tracks_dict(self):
        """Return all Plex tracks in a dictionary keyed on file path."""

        music = self.server.library.section('Music')

        print("[INFO] Loading Plex music library in memory. This may take a while...")
        plexLibrary = music.searchTracks()
        plexLibraryCount = len(plexLibrary)
        print("[INFO] Total number of Plex tracks: ", plexLibraryCount)
        #time.sleep(2)

        plexTracks = {}

        for track in plexLibrary:
            path = normalizeTrackPath(track.media[0].parts[0].file)
            plexTracks[path] = track

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
            if is_song_on_disk(song):
                path = normalizeTrackPath(song.location)
                itunesSongs[path] = song

        #del itunesLibrary

        print("[INFO] Total number of iTunes track file entries: ", len(itunesSongs))

        return itunesSongs

def normalizeTrackPath(path):
    if path.startswith('Volumes/'):
        path = '/' + path
    return unicodedata.normalize('NFC', os.path.normpath(path))

def is_song_on_disk(song):
    if not song.location:
        return False
    return song.location.startswith('Volumes/')

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

    assert plex_track.addedAt <= CURRENT_DATE
    assert plex_track.addedAt > OLDEST_DATE

    if plex_track.index:
        assert int(plex_track.index) >= 0

    if plex_track.lastViewedAt is not None:
        # assert plex_track.lastViewedAt <= CURRENT_DATE
        assert plex_track.lastViewedAt > OLDEST_DATE

    # title (str) - Artist, Album or Track title. (Jason Mraz, We Sing, Lucky, etc.)
    # originalTitle (str) - Track artist.
    # titleSort (str) - Title to use when sorting (defaults to title).

    # viewCount (int) - Count of times this item was accessed.
    assert plex_track.viewCount >= 0
