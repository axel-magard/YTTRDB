# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from pytube import Playlist


URL = "https://www.youtube.com/watch?v=%s"
URL_PLAYLIST = "https://www.youtube.com/playlist?list=%s"

def analyzeURL(url):
    video_id = ""
    pl_id = ""
    for w in url.split("?")[-1].split("&"):
        kw, v = w.split("=")
        if kw == "list":
            pl_id = v
        if kw == "v":
            video_id = v
    return(video_id,pl_id)

def getVideoTitle(video_id):
    url = URL % video_id
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    return(soup.title.text)

def getVideosInPlaylist(pl_id):
    videos = []
    url = URL_PLAYLIST % pl_id
    # Retrieve URLs of videos from playlist
    playlist = Playlist(url)
    for p in playlist:
        videos.append(p.split("=")[-1])
    return(videos)