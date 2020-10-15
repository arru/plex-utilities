set -e
git clone https://github.com/liamks/libpytunes.git libpytunes-checkout
ln -s libpytunes-checkout/libpytunes .
pip3 install --user plexapi
pip3 install --user mutagen
brew install --user ffmpeg
