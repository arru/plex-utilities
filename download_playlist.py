import sys
import shutil
import subprocess
import re
import os.path
from datetime import datetime
from distutils.dir_util import copy_tree

import ImportUtils

#TODO: Library.recentlyAdded(100) / .onDeck() / .all()

#TODO:
# destination config:
# playlist name(s)
# supported audio_formats (mime?)
# conversion audio_format

supported_formats = ['mp3:mp3']

# https://trac.ffmpeg.org/wiki/Encode/MP3
transcode_quality = 1
transcode_extension = "mp3"

DOWNLOAD_TMP = '/tmp/plex_playlist_download/'

CLEAN_FILE_CHARS_RE = re.compile(r'[^A-Za-z0-9\/\. ]+')
def clean_string(dirty_string):
    return CLEAN_FILE_CHARS_RE.sub('_', dirty_string).strip('_')

download_playlist_name = sys.argv[1] #.lower()
assert len(download_playlist_name) > 0

export_directory = sys.argv[2]
assert os.path.isdir(export_directory), "Output folder does not exist"

CONFIGURATION = ImportUtils.get_configuration()

plex = ImportUtils.PlexWrapper(CONFIGURATION)
#PLEX_TRACKS = plex.server.library.section('Music').searchTracks()
MUSIC_SECTION = plex.server.library.section('Music')

#TODO: permissive playlist name matching?

print ("Getting playlist '%s' from Plex server" % download_playlist_name)
download_playlist = plex.server.playlist(download_playlist_name)
playlist_items = download_playlist.items()
download_directory = os.path.join(DOWNLOAD_TMP, clean_string(download_playlist_name))
os.makedirs(download_directory, exist_ok=True)

downloaded_files = []
transcode_input_files = []

print ("Downloading %d tracks" % len(playlist_items))

for track in playlist_items:
    assert len(track.media) == 1
    media = track.media[0]
    audio_format = "%s:%s" % (media.audioCodec, media.container)
    download_paths = track.download(savepath=download_directory, keep_original_name=False)
    assert len(download_paths) == 1
    track_path = download_paths[0]
    if not audio_format in supported_formats:
        transcode_input_files.append(track_path)
        
    downloaded_files.append(track_path)

assert len (downloaded_files) > 0
assert len (transcode_input_files) <= len (downloaded_files)

print ("Copying files")

for dl_file in downloaded_files:
    if dl_file in transcode_input_files:
        filename = os.path.splitext(os.path.basename(dl_file))[0]
      
        ff_args = ["ffmpeg", "-i"]
        ff_args.append(dl_file)
        ff_args.extend(["-ac", "2"])
        ff_args.extend(["-q:a", str(transcode_quality)])
        #TODO: supply acodec arg as well
        ff_args.append(clean_string(os.path.join(export_directory, "%s.%s" % (filename, transcode_extension))))
        assert subprocess.run(ff_args)
    else:
        basename = os.path.basename(dl_file)
        export_path = clean_string(os.path.join(export_directory, basename))
        # print ("copy %s %s" % (dl_file, export_path))
        assert shutil.copy(dl_file, export_path)

print ("Done! %d tracks downloaded to %s (of which %d were transcoded to %s)" % (len(downloaded_files), export_directory, len(transcode_input_files), transcode_extension))

shutil.rmtree(DOWNLOAD_TMP, ignore_errors=False)
