import ImportUtils

CONFIGURATION = ImportUtils.get_configuration()

plex = ImportUtils.PlexWrapper(CONFIGURATION)

print ("This deletes ALL your playlists (but no media). Are you sure?")
answer = input("Type 'sure' if you are:")

if answer == 'sure':
    for playlist in plex.api.playlists():
        playlist.delete()

    print ("All your playlists deleted. A nice day to start again!")
