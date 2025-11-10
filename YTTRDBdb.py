# -*- coding: utf-8 -*-
from youtube_transcript_api import YouTubeTranscriptApi, _errors
import sqlite3

def formatTS(value):
    m = value // 60
    s = value - 60 * (value // 60)
    return("%02d:%02d" % (m,s))

def create_tables(con, cur):
    cur.execute("CREATE TABLE content(video_id,ts,duration,text)")
    con.commit()
    cur.execute("CREATE TABLE videos(video_id,title)")
    con.commit()

def insert_values(con, cur, video_id, ts, duration, text):
    sql= """
        INSERT INTO content VALUES
            ('%s',%f,%f,'%s')
    """ % (video_id,ts,duration,text.replace("'","''"))
    try:
        cur.execute(sql)
        con.commit()
    except sqlite3.OperationalError as ex:
        if handleDBError(con,cur,sql,ex):
            insert_values(con,cur,video_id,ts,duration,text)

def insert_title(con, cur, video_id, title):
    sql= """
        INSERT INTO videos VALUES
            ('%s','%s')
    """ % (video_id,title)
    try:
        cur.execute(sql)
        con.commit()
    except sqlite3.OperationalError as ex:
        if handleDBError(con,cur,sql,ex):
            insert_title(con,cur,video_id,title)


def list_data(con, cur, searchPattern = ""):
    qry = "SELECT content.video_id, ts, text, (SELECT title from videos WHERE videos.video_id = content.video_id) FROM content "
    if searchPattern:
        qry += " WHERE text like '%" + searchPattern + "%' "
    try:
        res = cur.execute(qry)
    except sqlite3.OperationalError as ex:
        if handleDBError(con,cur,qry,ex):
            list_data(con,cur,searchPattern)
            return []
    else:
        data = res.fetchall()
    d = []
    # Convert row tuples to lists
    for row in data:
        d.append(list(row))
    if not d:
        return([["","","","Nothing found."]])
    # Format timestamps
    for r in d:
        r[1] = formatTS(r[1])
    return d

def list_videos(cur):
    qry = "SELECT video_id, count(*) FROM content group by video_id"
    res = cur.execute(qry)
    data = res.fetchall()
    d = []
    # Convert row tuples to lists
    for row in data:
        d.append(list(row))
    return d

def handleDBError(con,cur,sql,ex):
    if str(ex) == 'no such table: content':
        create_tables(con,cur)
        return 1
    else:
        print(sql)
        print(">>>%s<<<" % ex)
        return 0

def fetch_transcript(con,cur,video_id = "gnRfvaSTgG8", signal = None):
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=['de',])
    except _errors.TranscriptsDisabled:
        return(-1)
    size = 30
    duration = 0.0
    text = ""
    ts = -1
    cnt = 0

    for j in transcript:
        cnt += 1
        if signal:
            signal.emit(cnt/len(transcript))
        if ts == -1:
            ts = j.start
        duration += j.duration
        text += j.text + " "
        if duration > size:
            insert_values(con,cur,video_id,ts,duration,text)
            duration = 0.0
            text = ""
            ts = -1
    insert_values(con,cur,video_id,ts,duration,text)
