import ImportUtils
import re

CONFIGURATION = ImportUtils.get_configuration()

plex = ImportUtils.PlexWrapper(CONFIGURATION)

reg = re.compile(r"[\|\*\-\~\^\? ]*(.+)")

#TODO: integrate with playlist import
for playlist in plex.server.playlists():
    canonical_title_match = reg.match(playlist.title)
    canonical_title = canonical_title_match.group(1)

    new_title = "|%s" % (canonical_title)
    
    print("%s -> %s" % (playlist.title, new_title))
    playlist.edit(**{'title': new_title})
