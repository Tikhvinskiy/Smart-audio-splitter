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

SmartAudioSplitter is tested on Python >= 3.8 and ubuntu 22.04

Samples:

```Python
from SmartAudioSplitter import SmartAudioSplitter


"""Parameters:   full_filename, add_pause=True, pause_len=2000,
                 silence_len=500, level_dBFS='calc',
                 multiprocessing_on=True,
                 n_split=4, n_jobs=2, how='split_by_silence',
                 out_filename='part', format_='mp3', bitrate='128k',
                 tags=None, log_to_file=False, store=None"""

worker = SmartAudioSplitter('full_filename')
worker.run()


#or use tkinter GUI interface

from SmartAudioSplitterTk import SmartAudioSplitterTk


worker = SmartAudioSplitter()
worker.start()
```


<img src="https://github.com/Tikhvinskiy/Smart-audio-splitter/blob/main/screen1.jpg" width="80%">

<img src="https://github.com/Tikhvinskiy/Smart-audio-splitter/blob/main/screen2.jpg" width="80%">



   
