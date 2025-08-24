# PodFetch
A Python script for easy podcast downloading.

Place the script in an empty folder.

The script will require an .opml file in the same folder, this contains a list of your podcasts and their RSS feeds.
Many existing podcast apps can export a file of this type, or PodFetch can create one for you.
If creating a blank file, you'll need to add your own RSS feeds - PodFetch can do this, but you have to find the RSS url's yourself.
Podcastindex.org is a good search resource for this.

The script should run on any system that has Python installed.
On a mac, change the script's extension to .command, make it executable, and it will run with a double click.
Linux is probably similar.
Windows; I don't know. Run it how you usually run a python program.

The rest is pretty self-explanatory.
Podcast episodes, when downloaded, will appear in a subfolder named after the podcast.
