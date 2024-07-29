# Smart Audio Splitter
SmartAudioSplitter splits large audio files into sections by silence. Contains audio processing functions based on pydub, ffmpeg, ffprobe. There is a multiprocessing mode.


### App.

- SmartAudioSplitter.py - main app uses pydub, ffmpeg, ffprobe
- SmartAudioSplitterTk.py -  the class that inherits methods from SmartAudioSplitter class.
   SmartAudioSplitterTk uses the standard Python interface to the Tcl/Tk GUI toolkit.
   Tkinter are available on most Unix platforms, including macOS, as well as on Windows systems.

### Installation.

Sometimes Python installations [don't include](https://stackoverflow.com/questions/76105218/why-does-tkinter-or-turtle-seem-to-be-missing-or-broken-shouldnt-it-be-part) Tkinter components. 
On Ubuntu and Debian based systems use this:
 - sudo apt-get install python3-tk

SmartAudioSplitter uses pydub, so you need install pydub (tested on 0.25.1 version):

- pip install pydub==0.25.1

FFmpeg, ffprobe is a part of the Ubuntu packages. If you dont have ones use this:

- sudo apt-get install ffmpeg

Samples:

<img src="https://github.com/Tikhvinskiy/Smart-audio-splitter/blob/main/screen1.jpg" width="80%">

<img src="https://github.com/Tikhvinskiy/Smart-audio-splitter/blob/main/screen2.jpg" width="80%">



   
