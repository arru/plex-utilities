import sys
import shutil
import subprocess
import re
import os.path

from configparser import ConfigParser
from datetime import datetime

import ImportUtils

#TODO: Library.recentlyAdded(100) / .onDeck() / .all()

#TODO:
# destination config:
# playlist name(s)
# supported audio_formats (mime?)
# conversion audio_format

DOWNLOAD_TMP = '/tmp/plex_playlist_download/'

CLEAN_FILE_CHARS_RE = re.compile(r'[^A-Za-z0-9\/\. ]+')
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

for download_playlist_name in download_playlist_names:
    print ("Getting playlist '%s' from Plex server" % download_playlist_name)
    #TODO: permissive playlist name matching?
    download_playlists.append(plex.server.playlist(download_playlist_name))

assert len(download_playlists) == len(download_playlist_names)
    
for download_playlist in download_playlists:
    playlist_items = download_playlist.items()

    download_directory = os.path.join(DOWNLOAD_TMP, clean_string(download_playlist.title))
    os.makedirs(download_directory, exist_ok=True)
    
    playlist_directory = os.path.join(export_directory, clean_string(download_playlist.title))

    downloaded_files = []
    transcode_input_files = []

    for track in playlist_items:
        assert len(track.media) == 1
        media = track.media[0]
        audio_format = (media.audioCodec, media.container)
        download_paths = track.download(savepath=download_directory, keep_original_name=False)
        assert len(download_paths) == 1
        track_path = download_paths[0]
        if not audio_format in SUPPORTED_FORMATS:
            transcode_input_files.append(track_path)
            
        downloaded_files.append(track_path)

    assert len (downloaded_files) > 0
    assert len (transcode_input_files) <= len (downloaded_files)

    print ("Copying files")
    
    os.makedirs(playlist_directory, exist_ok=True)

    for dl_file in downloaded_files:
        if dl_file in transcode_input_files:
            #TODO: acodec copy if only container differs
            filename = os.path.splitext(os.path.basename(dl_file))[0]
          
            ff_args = ["ffmpeg", "-i"]
            ff_args.append(dl_file)
            ff_args.extend(["-c:a", transcode_codec])
            ff_args.extend(["-ac", "2"])
            ff_args.extend(["-q:a", str(transcode_quality)])
            #TODO: supply acodec arg as well
            ff_args.append(clean_string(os.path.join(playlist_directory, "%s.%s" % (filename, transcode_extension))))
            assert subprocess.run(ff_args)
        else:
            basename = os.path.basename(dl_file)
            export_path = clean_string(os.path.join(playlist_directory, basename))
            # TODO: don't copy if exists
            # print ("copy %s %s" % (dl_file, export_path))
            assert shutil.copy(dl_file, export_path)

print ("Done! %d tracks downloaded to %s (of which %d were transcoded to %s)" % (len(downloaded_files), export_directory, len(transcode_input_files), transcode_extension))

shutil.rmtree(DOWNLOAD_TMP, ignore_errors=False)
