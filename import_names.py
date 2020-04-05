#!/usr/local/bin/python3

# https://python-plexapi.readthedocs.io/en/latest/modules/media.html
# https://github.com/liamks/libpytunes/blob/master/README.md

from os import path
import re
import plexapi

import ImportUtils

CONFIGURATION = ImportUtils.get_configuration()


ARTIST_DASH_TITLE_RE = re.compile(r"^^([^\d\(\) ]{2,}[^-\(\)]+) - (.+)$")

unknown_artist_playlist_items = []

def album_has_multiple_artists(plex_album):
    tracks = plex_album.tracks()
    for track in tracks:
        if track.originalTitle:
            common_artist = track.originalTitle
            break
    
    for track in tracks:
        if track.originalTitle:
            if track.originalTitle != common_artist:
                return False
                
    return True


def match_plex_artist(candidate_artist):
    if not candidate_artist:
        return None
        
    artist_search = MUSIC_SECTION.searchArtists(title=itunes_track.artist, maxresults=1)
    if len(artist_search) == 1:
        matched_artist = artist_search[0]
        matched_artist_name = matched_artist.title
        if close_enough(matched_artist_name, itunes_track.artist):
            return matched_artist
        
    return None
    
def close_enough(left, right):
    if not left or not right:
        return False
    
    left_filtered = re.sub(r"\W", '', left).lower()
    right_filtered = re.sub(r"\W", '', right).lower()
    
    if left_filtered.find(right_filtered) > -1:
        return True
    
    if right_filtered.find(left_filtered) > -1:
        return True
        
    return False
    
def format_replacement(replacement):
    if replacement:
        lock_marker = ""
        if replacement[1]:
            lock_marker = "(L)"
        
        return ("\t\t––>\t%s %s" % (replacement[0], lock_marker))
    else:
        return ""

plex = ImportUtils.PlexWrapper(CONFIGURATION)
PLEX_TRACKS = plex.server.library.section('Music').searchTracks()
MUSIC_SECTION = plex.server.library.section('Music')

itunes = ImportUtils.ItunesWrapper(CONFIGURATION)
itunes_tracks = itunes.get_tracks_dict()

del itunes

libraryMisses = 0

for plex_track_real in PLEX_TRACKS:
    plex_path = plex_track_real.media[0].parts[0].file

    itunes_track = None

    if plex_path in itunes_tracks:
        itunes_track = itunes_tracks[plex_path]
        assert path.isfile(plex_path)
    else:
        # print("'%s' not found in itunes_tracks" % plex_path)
        libraryMisses += 1
        continue

    plex_track = plex_track_real

    bad_title = plex_track.title.lower() in ImportUtils.EMPTY_TRACK_TITLES
    bad_album = plex_track.album() is None or plex_track.album().title.lower() in ImportUtils.EMPTY_ALBUM_TITLES and itunes_track.album is not None
    bad_track_artist = plex_track.originalTitle is None
    various_album = plex_track.album() is not None and len(plex_track.album().tracks()) > 1 and plex_track.artist().title == 'Various'
    bad_album_artist = plex_track.artist() is None or plex_track.artist().title.lower() in ImportUtils.EMPTY_ARTIST_NAMES
    #TODO: run dash filter on a curated "needs attention" playlist!
    artist_dash_title_match = ARTIST_DASH_TITLE_RE.match(itunes_track.name)

    album_issue_marker = "_"
    
    update_title = None
    update_track_artist = None
    update_album_artist = None
    update_album_title = None
        
    if various_album: # or itunes_track.compilation:
        if itunes_track.compilation:
            album_issue_marker = "W"
        else:
            album_issue_marker = "V"
            
        if bad_track_artist:
            #TODO copy resolved thing here
            if itunes_track.artist:
                update_track_artist = (str(itunes_track.artist).title(), True)
                matched_artist = match_plex_artist(itunes_track.artist)
                if matched_artist:
                    update_track_artist = (matched_artist.title, False)
                    
                album_issue_marker = "v"
                assert len(update_track_artist[0]) > 0
            else:
                album_issue_marker = "u"
                
    if bad_album_artist:
        album_issue_marker = "P"

        matched_artist = match_plex_artist(itunes_track.artist)
        matched_artist_name = "-"
        
        if matched_artist:
            update_album_artist = (matched_artist.title, True)
            album_issue_marker = "M"
        else:
            album_issue_marker = "U"
            
    if artist_dash_title_match:
        album_issue_marker = "D"
        
        matched_artist = None
        matched_artist = match_plex_artist(artist_dash_title_match.group(1))
            
        resolved_artist = str(artist_dash_title_match.group(1)).title()
        if matched_artist:
            resolved_artist = matched_artist.title
        
        if bad_album_artist:
            update_album_artist = (resolved_artist, False)
        
        if bad_track_artist and (various_album or not close_enough(resolved_artist, plex_track.artist().title)):
            update_track_artist = (resolved_artist, False)
            
        if (various_album and bad_track_artist) or close_enough(plex_track.artist().title, artist_dash_title_match.group(1)) or close_enough(itunes_track.artist, artist_dash_title_match.group(1)):
            update_title = (str(artist_dash_title_match.group(2)).title(), False)
    
    elif bad_title and itunes_track.name:
        album_issue_marker = "T"
        update_title = (str(itunes_track.name).title(), True)
        assert len(update_title[0]) > 0
    
    if bad_album and itunes_track.album:
        album_issue_marker = "A"
        update_album_title = (itunes_track.album, True)
        
    if update_title or update_track_artist or update_album_artist or update_album_title:
        plex_album = "(None)"
        if plex_track.album():
            plex_album = plex_track.album().title
            
        print ("%d\t\t|%s|%s" % (plex_track.ratingKey, plex_track.title, format_replacement(update_title)))
        print ("\t\t|%s|%s" % (plex_track.originalTitle, format_replacement(update_track_artist)))
        print ("\t\t|%s|%s" % (plex_track.artist().title, format_replacement(update_album_artist)))
        print ("\t\t|%s|%s" % (plex_album, format_replacement(update_album_title)))
        print()
    
    if update_title:
        plex_track.edit(**{'title.value': update_title[0]})
        plex_track.edit(**{'title.locked': int(update_title[1])})

    if update_track_artist:
        plex_track.edit(**{'originalTitle.value': update_track_artist[0]})
        plex_track.edit(**{'originalTitle.locked': int(update_track_artist[1])})
    if update_album_artist:
        print ("TODO update_album_artist")
    
    if update_album_title:
        print ("TODO update_album_title")

    if ((bad_title or artist_dash_title_match) and not update_title) or (bad_track_artist and various_album and not update_track_artist) or (bad_album_artist and bad_track_artist):
        unknown_artist_playlist_items.append(plex_track)

playlist_title = "Album, artist, title needs attention"
try:
    unknown_artist_playlist = plex.server.playlist(playlist_title)
    unknown_artist_playlist.delete()
except plexapi.exceptions.NotFound:
    pass

plexapi.playlist.Playlist.create(plex.server, playlist_title, items=unknown_artist_playlist_items, section=MUSIC_SECTION)

if libraryMisses > 0:
    print ("[WARNING] %d Plex tracks not found in iTunes metadata" % libraryMisses)
