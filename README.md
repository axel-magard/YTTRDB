# YTTRDB - Youtube Videos Transcript Database Tool
YTTRDB is a tool to capture and store transcripts from youtube videos and make those searchable. Once a text snippet has been found the corresponding video can be started with a simple click at the right time stamp.

  ## Implementation
  YTTRDB is written in Python and used
  * PyQt6 for the Graphical User Interface.
  * [The excellent Python API package by Jonas Depoix](https://github.com/jdepoix/youtube-transcript-api) is used to fetch youtube video
  transacripts for a given video.
  * [PyTube](https://github.com/pytube/pytube) is used to retrieve video titles.
  * SqLite3 is used a databse backend.

  ## Installation

  1. Clone this git repo
  2. Install missing python packages:

  ```
  pip install pyqt6
  pip install youtube_transcript_api
  pip install pytube
  ```


  ## Usage
  Start with this command:
  ```
  python -W ignore YTTRDB.py
  ```

  The main windows will be shown and lists all transcript records stored so far. For each record it shows video title and timestamp. When a record is selected the text of the transcript at the given time stamp is displayed on the right.
  
  ![YTTRDB Main Window](/html/images/2025-03-07%2009_01_32-YTTRDB%20-%20Youtube%20Videos%20Transcript%20Database%20Tool.png)
  
  The two black arrow buttons can be used to navigate back- and forward through the transcript records. The red play button will open your system browser and start playing the corresponding video at the given timestamp.
  Use File memu entry "Add Video ..." to add transcript(s) of additional videos. A youtube video id, url, or playlist url can be specified. Click OK to continue. 

  ![YTTRDB Add Video Dialog](/html/images/2025-03-07%2009_51_19-YTTRDB%20-%20Youtube%20Videos%20Transcript%20Database%20Tool.png)
  
  When a playlist url has been specified all the videos found in that playlist will be added to the YTTRDB database.


