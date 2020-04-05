import sys
import shutil
import subprocess
import re
import os.path
import os
import unicodedata

from configparser import ConfigParser

import mutagen.mp3
import mutagen.apev2
import mutagen.mp4

import ImportUtils

#TODO: Library.recentlyAdded(100) / .onDeck() / .all() / all tracks by artist

DOWNLOAD_TMP = '/tmp/plex_playlist_download/'
DELETE_REMOVED_TRACKS = True

PLAYLIST_FOLDER_RE = re.compile(r'(.*\|)?(.+)')

CLEAN_FILE_CHARS_RE = re.compile(r'[^A-Za-z0-9!åäöÅÄÖÜüßéÉ\-\.\(\) ]+')
def clean_string(dirty_string):
    return unicodedata.normalize('NFD', CLEAN_FILE_CHARS_RE.sub('_', dirty_string).strip('_'))


export_directory = os.path.abspath(sys.argv[1])
assert os.path.isdir(export_directory), "Output folder does not exist"

DL_CONFIGURATION = ConfigParser()
DL_CONFIGURATION.read(os.path.join(export_directory, "plex_download.cfg"))

# https://trac.ffmpeg.org/wiki/Encode/MP3
transcode_quality = DL_CONFIGURATION.get('Format', 'quality', fallback=3)
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

class ExistingTrack():
    name = None
    dir_path = None
    
    @classmethod
    def get_if_valid(_, full_path):
        _, extension = os.path.splitext(full_path)
        extension = extension[1:]
        for _, sext in SUPPORTED_FORMATS:
            if extension == sext:
                return ExistingTrack(full_path)
                
        return None
        
    def __init__(self, full_path):
        self.dir_path, self.name = os.path.split(full_path)
        assert os.path.isfile(self.path())
        
    def path(self):
        assert self.dir_path
        assert self.name
        
        return os.path.join(self.dir_path, self.name)
        
    def delete(self):
        assert DELETE_REMOVED_TRACKS
        
        os.remove(self.path())
        
        
class TrackExportOp():
    plex_track = None
    transcode_codec = None
    download_container = None
    
    hash = None
    download_path = None
    export_name = None
    
    title = None
    artist = None
    album = None
    
    def __init__(self, plex_track):
        self.plex_track = plex_track
        
        if self.plex_track.title:
            self.title = self.plex_track.title
        else:
            self.title = "Untitled %d" % self.plex_track.ratingKey
        
        if self.plex_track.originalTitle and self.plex_track.originalTitle.lower() not in ImportUtils.EMPTY_ARTIST_NAMES:
            self.artist = self.plex_track.originalTitle
        elif self.plex_track.artist().title.lower() not in ImportUtils.EMPTY_ARTIST_NAMES:
            self.artist = self.plex_track.artist().title

        if self.plex_track.album().title.lower() not in ImportUtils.EMPTY_ALBUM_TITLES:
            self.album = self.plex_track.album().title
        
        assert len(self.plex_track.media) == 1
        media = self.plex_track.media[0]
        audio_format = (media.audioCodec, media.parts[0].container)
        self.download_container = media.container
        assert self.download_container
        if audio_format not in SUPPORTED_FORMATS:
            self.transcode_codec = transcode_codec
            if media.audioCodec == self.transcode_codec:
                self.transcode_codec = 'copy'
                
        self.hash = media.id
                
        self.export_name = clean_string(self.title)
        
        if self.artist:
            self.export_name += " - %s" % clean_string(self.artist)
                
        self.export_name += "."
                    
        if self.transcode_codec:
            self.export_name += transcode_extension
        else:
            self.export_name += self.download_container
        
    def download(self):
        download_name = clean_string("%s.%s" % (self.hash, self.download_container))
        self.download_path = os.path.join(DOWNLOAD_TMP, download_name)
        if not os.path.isfile(self.download_path):
            download_paths = self.plex_track.download(savepath=DOWNLOAD_TMP, keep_original_name=False)
            assert len(download_paths) == 1
            
            os.rename(download_paths[0], self.download_path)
            
            if not self.transcode_codec:
                self.__write_tags(self.download_container, self.download_path)
             
    def __write_tags(self, container, file):
        if container == 'mp3':
            try:
                tag_file = mutagen.id3.ID3(file)
            except mutagen.id3.ID3NoHeaderError:
                tag_file = mutagen.id3.ID3()
            tag_file.add(mutagen.id3.TIT2(text=self.title))
            if self.album:
                tag_file.add(mutagen.id3.TALB(text=self.album))
            if self.artist:
                tag_file.add(mutagen.id3.TPE1(text=self.artist))
            tag_file.save(file)
        elif container == 'aac':
            tag_file = mutagen.apev2.APEv2File(file)
            try:
                tag_file.add_tags()
            except mutagen.apev2.error:
                # error if file already has tags
                pass
        
            # http://wiki.hydrogenaud.io/index.php?title=APE_key
            tag_file.tags['Title'] = self.title
            if self.album:
                tag_file.tags['Album'] = self.album
        
            if self.artist:
                tag_file.tags['Artist'] = self.artist
        
            tag_file.save()
            
        elif container in ['mp4', 'm4a']:
            tag_file = mutagen.mp4.MP4(file)
            try:
                tag_file.add_tags()
            except mutagen.mp4.error:
                # error if file already has tags
                # print(tag_file.tags)
                pass
                
            tag_file.tags['©nam'] = self.title
            if self.album:
                tag_file.tags['©alb'] = self.album
        
            if self.artist:
                tag_file.tags['©ART'] = self.artist
        
            tag_file.save()

    def export_path(self, playlist_directory):
        return os.path.join(playlist_directory, self.export_name)
        
    def export(self, playlist_directory):
        export_path = self.export_path(playlist_directory)
        
        if self.transcode_codec:
            transcode_path = os.path.join(DOWNLOAD_TMP, "%s.%s" % (self.hash, transcode_extension))
            if not os.path.isfile(transcode_path):
                ff_args = ["ffmpeg", "-i"]
                ff_args.append(self.download_path)
                ff_args.append('-vn')
                ff_args.extend(["-c:a", self.transcode_codec])
                ff_args.extend(["-ac", "2"])
                ff_args.extend(["-q:a", str(transcode_quality)])
                ff_args.append(transcode_path)
                
                subprocess.run(ff_args)
                
            self.__write_tags(transcode_extension, transcode_path)
            assert shutil.copy(transcode_path, export_path)

        else:
            # print ("copy %s %s" % (dl_file, export_path))
            assert shutil.copy(self.download_path, export_path)
            
    def __str__(self):
        return ("%s\t/\t%s" % (self.plex_track.title, self.plex_track.grandparentTitle))

os.makedirs(DOWNLOAD_TMP, exist_ok=True)

for download_playlist in download_playlists:
    stripped_title = PLAYLIST_FOLDER_RE.match(download_playlist.title).group(2)
    assert stripped_title
    playlist_directory = os.path.join(export_directory, clean_string(stripped_title))
    os.makedirs(playlist_directory, exist_ok=True)

    playlist_items = download_playlist.items()
    remaining_items = {}
    
    for (dirpath, dirnames, filenames) in os.walk(playlist_directory):
        for file in filenames:
            file_path = os.path.join(playlist_directory, file)
            
            existing_track = ExistingTrack.get_if_valid(file_path)
            if existing_track:
                remaining_items[unicodedata.normalize('NFD', existing_track.name)] = existing_track
        break
    
    print ("**** Exporting %s" % download_playlist.title)
    for item in playlist_items:
        track_op = TrackExportOp(item)
        
        if not track_op.export_name in remaining_items.keys():
            track_op.download()
            track_op.export(playlist_directory)
            
            print ("   + %s" % str(track_op))
        else:
            # Preexisting track, skip
            del(remaining_items[track_op.export_name])
        
    if DELETE_REMOVED_TRACKS:
        print ("**** Deleting removed tracks")
        assert len(playlist_items) > len(remaining_items)
        for _, existing_track in remaining_items.items():
            print ("   - %s" % existing_track.path())
            existing_track.delete()

print("**** All done!")#%d tracks downloaded to %s (of which %d were transcoded to %s)" % (len(downloaded_files), export_directory, len(transcode_input_files), transcode_extension))
