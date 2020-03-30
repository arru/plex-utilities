import sys
import shutil
import subprocess
import re
import os.path

from configparser import ConfigParser
from datetime import datetime

import ImportUtils

#TODO: Library.recentlyAdded(100) / .onDeck() / .all() / all tracks by artist

DOWNLOAD_TMP = '/tmp/plex_playlist_download/'

PLAYLIST_FOLDER_RE = re.compile(r'(.*\|)?(.+)')

CLEAN_FILE_CHARS_RE = re.compile(r'[^A-Za-z0-9\/\-\. ]+')
def clean_string(dirty_string):
    return CLEAN_FILE_CHARS_RE.sub('_', dirty_string).strip('_')


export_directory = sys.argv[1]
assert os.path.isdir(export_directory), "Output folder does not exist"

DL_CONFIGURATION = ConfigParser()
DL_CONFIGURATION.read(os.path.join(export_directory, "plex_download.cfg"))

# https://trac.ffmpeg.org/wiki/Encode/MP3
transcode_quality = DL_CONFIGURATION.get('Format', 'quality', fallback=1)
transcode_codec = DL_CONFIGURATION.get('Format', 'codec', fallback='mp3')
transcode_extension = DL_CONFIGURATION.get('Format', 'container', fallback='mp3')

SUPPORTED_FORMATS = []
for format_entry in ImportUtils.unmarshal_cfg_list(DL_CONFIGURATION.get('Format', 'Supported formats')):
    SUPPORTED_FORMATS.append(tuple(format_entry.split('/')))

transcode_spec = (transcode_codec, transcode_extension)
assert len(SUPPORTED_FORMATS) > 0
assert transcode_spec in SUPPORTED_FORMATS

download_playlist_names = ImportUtils.unmarshal_cfg_list(DL_CONFIGURATION.get('Source', 'playlists'))

CONFIGURATION = ImportUtils.get_configuration()

plex = ImportUtils.PlexWrapper(CONFIGURATION)
MUSIC_SECTION = plex.server.library.section('Music')

download_playlists = []

print ("Getting playlists from Plex server:")
for download_playlist_name in download_playlist_names:
    print (download_playlist_name)
    #TODO: permissive playlist name matching?
    download_playlists.append(plex.server.playlist(download_playlist_name))

assert len(download_playlists) == len(download_playlist_names)

class TrackExportOp():
    plex_track = None
    transcode_codec = None
    download_path = None
    export_path = None
    
    def __init__(self, plex_track):
        self.plex_track = plex_track
        assert len(self.plex_track.media) == 1
        media = self.plex_track.media[0]
        audio_format = (media.audioCodec, media.parts[0].container)
        if audio_format not in SUPPORTED_FORMATS:
            self.transcode_codec = transcode_codec
            if media.audioCodec == self.transcode_codec:
                self.transcode_codec = 'copy'
        
    def download(self):
        #TODO: use original name and determine path before this step
        # so that already DL'd tracks can be skipped
        
        download_paths = self.plex_track.download(savepath=DOWNLOAD_TMP, keep_original_name=False)
        assert len(download_paths) == 1
        self.download_path = download_paths[0]
        #TODO: update ID3 tags from plex data

    def export(self, playlist_directory):
        if self.transcode_codec:
            # TODO: don't encode if exists
            filename = os.path.splitext(os.path.basename(self.download_path))[0]
          
            ff_args = ["ffmpeg", "-i"]
            ff_args.append(self.download_path)
            ff_args.append('-vn')
            ff_args.extend(["-c:a", self.transcode_codec])
            ff_args.extend(["-ac", "2"])
            ff_args.extend(["-q:a", str(transcode_quality)])
            ff_args.append(clean_string(os.path.join(playlist_directory, "%s.%s" % (filename, transcode_extension))))
            subprocess.run(ff_args)
        else:
            # TODO: don't copy if exists
            basename = os.path.basename(self.download_path)
            self.export_path = clean_string(os.path.join(playlist_directory, basename))
            # print ("copy %s %s" % (dl_file, export_path))
            assert shutil.copy(self.download_path, self.export_path)
            
    def __str__(self):
        return ("%s\t/\t%s" % (self.plex_track.title, self.plex_track.grandparentTitle))

os.makedirs(DOWNLOAD_TMP, exist_ok=True)

for download_playlist in download_playlists:
    stripped_title = PLAYLIST_FOLDER_RE.match(download_playlist.title).group(2)
    assert stripped_title
    playlist_directory = os.path.join(export_directory, clean_string(stripped_title))
    os.makedirs(playlist_directory, exist_ok=True)

    playlist_items = download_playlist.items()
    
    print ("Exporting %s" % download_playlist.title)
    for item in playlist_items:
        track_op = TrackExportOp(item)
        track_op.download()
        track_op.export(playlist_directory)
        
        print ("**** Exported track %s" % str(track_op))

print("All done!")#%d tracks downloaded to %s (of which %d were transcoded to %s)" % (len(downloaded_files), export_directory, len(transcode_input_files), transcode_extension))
