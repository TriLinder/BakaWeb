from dateutil import parser
from pathlib import Path
from bakaapi import *
import shelve
import time
import json

def getMarks(url, refresh_token, userID, forceRefresh) :
    s = shelve.open(str(Path("bakaAccounts/%s" % (userID))))

    try :
        if forceRefresh :
            raise KeyError
        marks = s["marks"]
    except KeyError :
        marks = requestAuthenticated(refresh_token, url, "/api/3/marks", {}, "get").decode("utf-8")
        marks = json.loads(marks)
        s["marks"] = marks
        s["marks_lastUpdate"] = round(time.time())
    
    s.close()
    return marks

def getLastUpadte(userID) :
    s = shelve.open(str(Path("bakaAccounts/%s" % (userID))))
    lastUpdate = s["marks_lastUpdate"]
    s.close()

    return lastUpdate

def getMarksForSubjects(marksJ) :

    subjects = []
    
    for subject in marksJ :
        abbrev = subject["Subject"]["Abbrev"]
        avrg = subject["AverageText"]
        name = subject["Subject"]["Name"]

        marks = []

        for mark in subject["Marks"] :
            date = round(parser.parse(mark["MarkDate"]).timestamp())
            caption = mark["Caption"]
            value = mark["MarkText"]
            weight = mark["Weight"]
            isPoints = mark["IsPoints"]
            maxPoints = mark["MaxPoints"]

            mark = {"date":date, "caption":caption, "value":value, "weight":weight, "isPoints":isPoints, "maxPoints":maxPoints}
            marks.append(mark)
        
        subject = {"abbrev":abbrev, "avrg":avrg, "marks":marks, "name":name}
        subjects.append(subject)
    
    return subjects

def subjectsToHtml(subjects) :
    
    html = ""

    mostMarks = -1

    for subject in subjects :
        lenght = len(subject["marks"])

        if lenght > mostMarks :
            mostMarks = lenght

    subjectI = 0

    for subject in subjects :
        subjectI += 1

        html = html + "<tr class='%s'> <th class='subject'>%s <br> %s </th>" % (["centerLine", "finalLine"][int(subjectI == len(subjects))], subject["name"], subject["avrg"])

        markI = 0

        for mark in subject["marks"] :
            markI += 1

            markDate = time.strftime("%d.%m.%Y", time.localtime(mark["date"]))

            markBoxClass = [["markBox", "markBoxFinal"], ["markBoxL", "markBoxFinalL"]][int(subjectI == len(subjects))][int(markI == mostMarks)]

            weight = mark["weight"]

            if weight == None :
                weight = ""

            if mark["isPoints"] :
                maxPoints = "/%d" % (mark["maxPoints"])
            else :
                maxPoints = ""

            html = html + "<th class='%s'><span class='weight' title='Weight: %s'>%s</span><br><b class='markValue' title='%s'>%s</b><span class='maxPoints'>%s</span><br><span class='caption'>%s</span><br><span class='date'>%s</span></th>" % (markBoxClass, str(weight), str(weight), mark["caption"], mark["value"], maxPoints, mark["caption"], markDate)

        for i in range(mostMarks - len(subject["marks"])) :
            emptyBoxClass = ["empty", "emtpyL"][int(subjectI == len(subjects))]
            html = html + "<th class='%s'></th>" % (emptyBoxClass)

        html = html + "</tr>"
    
    return html