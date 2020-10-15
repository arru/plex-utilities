Arru's Plex utilities
======================

What's this?
------------

ALL THESE ARE EXPERIMENTAL

Mainly to aid with importing iTunes metadata, and downloading files for offline playing on a hardware device like a car stereo, boom box, legacy mp3 player etc. The scripts can probably be useful as examples on how to use the Plex API since documentation is not very, shall we say, verbose.

Contents – various scripts
--------------------------

### download_playlist.py
Exports playlists and other library items to file ystem directories such as car head unit SD cards, boom boxes etc. Will also transcode any items that do not match the supported file types of the device. Items and transcoding is configured by a `plex_download.cfg` file placed in the export directory, see below.

### Download CFGs
Example download configurations for common use cases. For any random mp3 player you can just copy the one in the `MP3 player` folder and add your own items.

### flag_duplicates.py
Creates a playlist containing all tracks which are deemed duplicate (having same name, nearly same length, see code for details). This playlist is named _"Duplicates (lower bitrates)"_ and contains every duplicate **except** the one with the highest bitrate and highest quality codec. The idea being that, right after running this script, you can delete the tracks in this playlist to save space while keeping the highest-quality copy of that song.

### delete_all_playlists.py
Does what it says. This can be useful when testing out the playlist import. There is actually no way of doing this inside Plex without deleting playlists one-by-one.

### Profile
Not really a script, but a small gift if you're running a Yamaha MusicCast system and it won't play your Apple lossless files


Contents – iTunes migration scripts
-----------------------------------

### import_metadata.py
Imports ratings from iTunes

### import_names.py
Imports artist/album/track names from iTunes
	
### import_playlists.py
Imports playlists from iTunes

### playlist_sort.py
Does not sort your playlists, however it will help you with sorting like this: when run, it will add | characters at the beginning of every playlist, so those existing ones will sort after any playlists added onwards. If you do this right after importing from iTunes you can distinguish your new playlists from imported ones in a nice way. The | character is also used as a "hierarchy" delimiter with other scripts here, giving you a nice substitute for iTunes playlist folders.

Contents – helper scripts
--------------------------

### ImportUtils.py
Helper script for the others. Don't run it directly.

### install.sh
Run this to install 3rd party dependencies for these scripts

### itunes_plex.default.cfg
Copy this file name it `itunes_plex.cfg` and put your Plex and iTunes (if applicable) configuration here

### get_token.py
Run this and log in to your Plex account to get an API token which you can then put in  `itunes_plex.cfg` to make the gears of these scripts run smoothly.

### README.md
You are here

plex_download.cfg syntax
------------------------
_See files in Download CFGs folder for examples of these settings values_

### `[Format]` section

`codec:` transcoding codec to use  
`container:` container format for transcoding output.  
`quality:` quality setting when transcoding. These work differently for different transcoding formats, see example configurations and FFMPEG documentation.
`supported formats:` list of combinations of codec/container that the destination media player supports  

### `[Source]` section

#### Playlist
`/playlist/Road trip 2020` Get a named Plex playlist.  
Also, if you don't a prefix (the thing starting with / ) the script will assume that you want a playlist with that name. In other words, for playlists you can skip `/playlist/` at the start if you want.

#### Year
`/year/1985`
Get all songs from this year

#### Albums
`/album/Hysteria/Def Leppard`
Get an album in the form `/album/TITLE/ARTIST`

#### Artist
`/artist/Tangerine Dream`
Get all tracks by an artist

#### Latest
`/latest/100`
Get the N latest tracks added to your Plex library.

Requirements
------------
-   Plex server set up somewhere
-   Plex account (not using any Plex Pass features that I'm aware of)
-   Python 3
-   Homebrew (for install script, dependencies can be manually installed just as well)
-   Python plexapi
-   libpytunes
-   mutagen
-   ffmpeg

All these except Python 3 and Plex itself will be installed by the `install.sh` script. These Plex scripts can be run by another computer talking to the Plex server, the machine running the script _does not need_ Plex server (or desktop client) installed.

Installation
------------
1.  run install.sh script
1.  run get_token.py (see instructions above) to get your Plex login token, then paste it at the appropriate line in `itunes_plex.cfg`
1.  if you're just starting with Plex and migrating from iTunes, start with the iTunes import scripts, then use playlist_sort.py if you wish (recommended)

License
-------
These scripts are copyright © 2020 Arvid Rudling. Licensed under the 3-Clause BSD License, se LICENSE file

Plex is a trademark of Plex, Inc. or its subsidiaries.
All other trademarks are the property of their respective owners.

The software is developed without any affiliation to the mentioned vendors.
