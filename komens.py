from dateutil import parser
from pathlib import Path
from bakaapi import *
import shelve
import json
import time

def getMsgs(url, refresh_token, userID, forceRefresh) :
    s = shelve.open(str(Path("bakaAccounts/%s" % (userID))))

    try :
        if forceRefresh :
            raise KeyError
        msgs = s["komensMsgs"]
    except KeyError :
        msgs = requestAuthenticated(refresh_token, url, "/api/3/komens/messages/received", {}, "post").decode("utf-8")
        
        try :
            msgs = json.loads(msgs)["Messages"]
        except KeyError : #Komens module disabled
            msgs = []
        
        s["komensMsgs"] = msgs
        s["komensMsgs_lastUpdate"] = round(time.time())

    s.close()
    return msgs

def getLastUpadte(userID) :
    s = shelve.open(str(Path("bakaAccounts/%s" % (userID))))
    lastUpdate = s["komensMsgs_lastUpdate"]
    s.close()

    return lastUpdate

def sortBySentDate(msg) :
    return msg[4]

def getMsgsInfo(msgs) :
    info = []

    for msg in msgs :
        title = msg["Title"]
        sender = msg["Sender"]["Name"]
        sentDate = msg["SentDate"]
        id = msg["Id"]
        
        sentDateEpoch = round(parser.parse(sentDate).timestamp())

        info.append([title, sender, id, sentDate, sentDateEpoch])
    
    info.sort(key=sortBySentDate, reverse=True)

    return info

def infoToHtml(msgs) :
    if len(msgs) == 0 :
        return "<tr><th>You have no messages.<th></tr>"
    
    html = ""

    for msg in msgs :
        title = msg[0]
        sender = msg[1]
        id = msg[2]
        sentDateEpoch = msg[4]

        sentDate = time.strftime("%d.%m.%Y %H:%M", time.localtime(sentDateEpoch))
        daysAgo = round((time.time()-sentDateEpoch)/60/60/24)

        html = html + "<tr><th class='title'><a href='komens-msg/%s'>%s</a></th> <th class='sender'>%s</th> <th class='sentDate'>%s, <i>%d days ago</i></th></tr>" % (id, title, sender, sentDate, daysAgo)
    
    return html

def getMsgInfo(id, msgs) :
    
    msg = None

    for tempMsg in msgs :
        if tempMsg["Id"] == id :
            msg = tempMsg
            break
    
    if not msg :
        raise KeyError
    

    title = msg["Title"]
    sender = msg["Sender"]["Name"]
    sentDate = msg["SentDate"]
    id = msg["Id"]
    body = msg["Text"].replace("script", "s_cript").replace("iframe", "if_rame")

    sentDateEpoch = round(parser.parse(sentDate).timestamp())

    return {"title": title, "sender": sender, "id": id, "sentDate": sentDate, "sentDateEpoch": sentDateEpoch, "body": body}