from collections import OrderedDict
from pathlib import Path
from bakaapi import *
import shelve
import time

dayNamesAbbr = ["Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat.", "Sun."]
dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def getTimetable(url, refresh_token, userID, forceRefresh) :
    s = shelve.open(str(Path("bakaAccounts/%s" % (userID))))

    try :
        if forceRefresh :
            raise KeyError
        timetable = s["timetable"]
    except KeyError :
        timetable = requestAuthenticated(refresh_token, url, "/api/3/timetable/permanent", {}, "get").decode("utf-8")
        s["timetable"] = timetable
        s["lastUpdate"] = int(time.time())
    
    s.close()
    return timetable

def getTimetableLastUpadte(userID) :
    s = shelve.open(str(Path("bakaAccounts/%s" % (userID))))
    lastUpdate = s["lastUpdate"]
    s.close()

    return lastUpdate

def getTeachers(jTimetable) :
    teachers = {}

    for teacher in jTimetable["Teachers"] :
        teachers[teacher["Id"]] = teacher["Name"]
    
    return teachers

def getSubjects(jTimetable) :
    subjects = {}

    for subject in jTimetable["Subjects"] :
        subjects[subject["Id"]] = subject["Abbrev"]
    
    return subjects

def getSubjectsFullName(jTimetable) :
    subjects = {}

    for subject in jTimetable["Subjects"] :
        subjects[subject["Id"]] = subject["Name"]
    
    return subjects

def getDays() :
    return dayNames

def htmlTimetable(jTimetable, highlight="none") :
    html = "<table style='width:100%'> <tr> <td></td>"

    subjects = getSubjects(jTimetable)

    maxHours = -1
    under1 = 0

    for hour in jTimetable["Hours"] :
        if int(hour["Caption"]) > maxHours :
            maxHours = int(hour["Caption"])
        if int(hour["Caption"]) < 1 :
            under1 += 1
        html = html + "<td class='caption'>%s.</td>" % (hour["Caption"])

    html = html + "</tr><tr> <td></td>"

    for hour in jTimetable["Hours"] :
        html = html + "<td class='time'>%s-%s</td>" % (hour["BeginTime"], hour["EndTime"])
    
    dayNumber = 0

    for day in jTimetable["Days"] :
        html = html + "</tr><tr> <td class='day'>%s</td>" % (dayNamesAbbr[day["DayOfWeek"]-1])
        lastHourID = -1

        dayLenght = 0
        hourNumber = 0
        dayNumber += 1

        for hour in day["Atoms"] :
            hourID = int(hour["HourId"])
            hourNumber += 1

            if not lastHourID == -1 :
                for i in range((hourID-1) - lastHourID) :
                    dayLenght += 1
                    html = html + "<td class='empty'>%s</td>" % ("")
            
            lastHourID = hourID
            subject = subjects[hour["SubjectId"]]
            dayLenght += 1

            coords = "%dx%d" % (dayNumber-1, hourNumber-1)
            if coords == highlight :
                html = html + "<td class='highlight'><a href='/timetable_details/%dx%d'>%s</a></td>" % (dayNumber-1, hourNumber-1, subject)
            else :    
                html = html + "<td class='subject'><a href='/timetable_details/%dx%d'>%s</a></td>" % (dayNumber-1, hourNumber-1, subject)
        
        dayLenght = dayLenght - under1
        for i in range(maxHours - dayLenght) :
            html = html + "<td class='empty'>%s</td>" % ("")
    
    html = html + "</table>"

    return html

def timetableDetails(coords, jTimetable) :
    if "x" in coords :
        coords = coords.split("x")

        coord1 = int(coords[0])
        coord2 = int(coords[1])

        subjectsAbbrev = getSubjects(jTimetable)
        subjectsFull = getSubjectsFullName(jTimetable)

        teachers = getTeachers(jTimetable)

        hour = jTimetable["Days"][coord1]["Atoms"][coord2]
        teacherID = hour["TeacherId"]
        subjectID = hour["SubjectId"]
    
    else :
        subjectID = coords

    fullName = subjectsFull[subjectID]
    abbrev = subjectsAbbrev[subjectID]
    teacher = teachers[teacherID]

    return [fullName, abbrev, teacher]

def compare(day1, day2, jTimetable) :
    day1Subjects = []
    day2Subjects = []

    subjectNames = getSubjectsFullName(jTimetable)
    
    for subject in jTimetable["Days"][day1]["Atoms"] :
       day1Subjects.append(subject["SubjectId"])

    for subject in jTimetable["Days"][day2]["Atoms"] :
       day2Subjects.append(subject["SubjectId"])
    
    remove = []
    add = []

    removeCoords = []
    addCoords = []

    i = 0

    for subject in day1Subjects :
        if not subject in day2Subjects :
            remove.append(subject)
            removeCoords.append("%dx%d" % (day1, i))
        i += 1
    
    i = 0

    for subject in day2Subjects :
        if not subject in day1Subjects :
            add.append(subject)
            addCoords.append("%dx%d" % (day2, i))
        i += 1

    remove = list(OrderedDict.fromkeys(remove))
    add = list(OrderedDict.fromkeys(add))

    removeNames = []
    addNames = []


    for subjectID in remove :
        removeNames.append(subjectNames[subjectID])
    
    for subjectID in add :
        addNames.append(subjectNames[subjectID])

    return [removeNames, addNames, removeCoords, addCoords]

def compareToHtml(compare) :
    remove = compare[0]
    add = compare[1]

    removeCoords = compare[2]
    addCoords = compare[3]

    maxLenght = len(remove)
    removeIsLonger = True

    if len(add) > maxLenght :
        maxLenght = len(add)
        removeIsLonger = False
    
    if removeIsLonger :
        for i in range(len(remove) - len(add)) :
            add.append("")
            addCoords.append("0x0")
    else :
        for i in range(len(add) - len(remove)) :
            remove.append("")
            removeCoords.append("0x0")
    
    html = ""

    for i in range((len(remove))) :
        html = html + "<tr>"
        html = html + "<th class='remove'><a class='table-link' href='/timetable_details/%s'>%s</a></th>" % (removeCoords[i], remove[i])
        html = html + "<th class='add'><a class='table-link' href='/timetable_details/%s'>%s</a></th>" % (addCoords[i], add[i])
        html = html + "</tr>"
    
    return html