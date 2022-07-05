from flask import Flask, redirect, render_template, request, session
from flask_session import Session
import timetable
import accounts
import bakaapi
import schools
import komens
import marks
import json
import time


#--------CONFIG--------#

allowCustomURLs = False #Might be a security risk, not recommended.

#----------------------#


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

#------------------------#

@app.get("/")
def root() :
    if not session.get("auth-token") :
        return redirect("/login")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    userInfo = json.loads(bakaapi.getUserInfo(url, refresh_token, userID, False))

    try :
        return render_template("main.html", name=userInfo["FullName"], accountType=userInfo["UserTypeText"])
    except :
        return redirect("/logout")

@app.get("/timetable")
def timetablePage(highlight_coords="none") :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    userInfo = json.loads(bakaapi.getUserInfo(url, refresh_token, userID, False))

    try :
        timetableJson = json.loads(timetable.getTimetable(url, refresh_token, userID, False))
        htmlTimetable = timetable.htmlTimetable(timetableJson, highlight=highlight_coords)
    except Exception as e :
        return render_template("timetable_error.html", error=str(e))

    lastUpdate = timetable.getTimetableLastUpadte(userID)
    lastUpdateText = time.strftime("%d.%m %H:%M", time.localtime(lastUpdate))

    return render_template("timetable.html", name=userInfo["FullName"], timetable=htmlTimetable, lastUpdate=lastUpdateText)

@app.get("/timetable-highlight/<coords>")
def timetablePageHighlight(coords) :
    return timetablePage(highlight_coords=coords)

@app.get("/timetable_details/<coords>")
def timetableDetailsPage(coords) :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    timetableJson = json.loads(timetable.getTimetable(url, refresh_token, userID, False))
    
    try :
        details = timetable.timetableDetails(coords, timetableJson)
    except IndexError :
        return redirect("/timetable")

    #userInfo = json.loads(bakaapi.getUserInfo(url, refresh_token, userID, False))
    return render_template("timetable_details.html", name=details[0], teacher=details[2], abbrev=details[1], coords=coords)

@app.get("/timetable_compare")
def timetableComparePage() :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    userInfo = json.loads(bakaapi.getUserInfo(url, refresh_token, userID, False))
    timetableJson = json.loads(timetable.getTimetable(url, refresh_token, userID, False))
    dayNames = timetable.getDays()

    #userInfo = json.loads(bakaapi.getUserInfo(url, refresh_token, userID, False))
    return render_template("timetable_compare.html", monday_name=dayNames[0], tuesday_name=dayNames[1], wednesday_name=dayNames[2], thursday_name=dayNames[3], friday_name=dayNames[4], saturday_name=dayNames[5], sunday_name=dayNames[6], visible="none")

@app.post("/timetable_compare")
def timetableCompareHanlder() :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    userInfo = json.loads(bakaapi.getUserInfo(url, refresh_token, userID, False))
    timetableJson = json.loads(timetable.getTimetable(url, refresh_token, userID, False))

    day1 = request.form["day1"]
    day2 = request.form["day2"]
    compared = timetable.compare(int(day1)-1, int(day2)-1, timetableJson)
    comparedHTML = timetable.compareToHtml(compared)
    dayNames = timetable.getDays()

    visible = True
    error = ""

    if len(compared[0]) + len(compared[1]) == 0 :
        visible = False
        error = "No diffrence between days."
    
    if day1 == day2 :
        error = "Comparing same day."

    #userInfo = json.loads(bakaapi.getUserInfo(url, refresh_token, userID, False))
    return render_template("timetable_compare.html", monday_name=dayNames[0], tuesday_name=dayNames[1], wednesday_name=dayNames[2], thursday_name=dayNames[3], friday_name=dayNames[4], saturday_name=dayNames[5], sunday_name=dayNames[6], compare=comparedHTML, error=error, visible=["none", "shown"][int(visible)])

@app.post("/timetable-reload")
def timetableReload() :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    json.loads(timetable.getTimetable(url, refresh_token, userID, True)) #<--- Forces a reload

    return redirect("/timetable")

#--------------------------------------------------#

@app.get("/komens")
def komensPage() :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    komensMsgs = komens.getMsgs(url, refresh_token, userID, False)
    msgsInfo = komens.getMsgsInfo(komensMsgs)
    msgsHtml = komens.infoToHtml(msgsInfo)

    lastUpdate = komens.getLastUpadte(userID)
    lastUpdateText = time.strftime("%d.%m %H:%M", time.localtime(lastUpdate))

    return render_template("komens.html", msgs=msgsHtml, lastUpdate=lastUpdateText)

@app.get("/komens-msg/<id>")
def komensMsg(id) :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    komensMsgs = komens.getMsgs(url, refresh_token, userID, False)

    try :
        msgInfo = komens.getMsgInfo(id, komensMsgs)
    except KeyError :
        return "Message not found."

    return render_template("komens_msg.html", body=msgInfo["body"], title=msgInfo["title"], sender=msgInfo["sender"])

@app.post("/komens-reload")
def komensReload() :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    komens.getMsgs(url, refresh_token, userID, True) #<----- Force reload

    return redirect("/komens")

#----------------------------------------------#

@app.get("/marks")
def marksPage() :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    marksJ = marks.getMarks(url, refresh_token, userID, False)["Subjects"]
    subjects = marks.getMarksForSubjects(marksJ)
    marksHtml = marks.subjectsToHtml(subjects)

    lastUpdate = marks.getLastUpadte(userID)
    lastUpdateText = time.strftime("%d.%m %H:%M", time.localtime(lastUpdate))

    return render_template("marks.html", marks=marksHtml, lastUpdate=lastUpdateText)

@app.post("/marks-reload")
def marksReload() :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    marks.getMarks(url, refresh_token, userID, True) #<---- Forces a refresh

    return redirect("/marks")

#----------------------------------------------#

@app.get("/choose-city")
def chooseCityPage() :
    if session.get("auth-token") :
        return redirect("/")

    cities = schools.getCities()
    htmlCities = schools.chooseCityHtml(cities)

    return render_template("chooseSchool.html", items=htmlCities, name="city")

@app.get("/city/<city>")
def citySearch(city) :
    if session.get("auth-token") :
        return redirect("/")

    search = schools.getSchools(city)

    if search == "invalidCity" :
        return redirect("/")

    htmlSchools = schools.chooseSchoolHtml(search)

    return render_template("chooseSchool.html", items=htmlSchools, name="school")

@app.get("/login-school/<city>/<id>")
def loginSchoolSelected(city, id) :
    if session.get("auth-token") :
        return redirect("/")
    
    id = id.strip()

    url = schools.getSchoolURL(city, id)

    if url == "invalid" :
        return redirect("/")

    return render_template("login.html", url=url, id="%s;%s" % (city, id), disableUrlBox=["disabled", ""][int(allowCustomURLs)])

@app.get("/login")
def loginPage() :
    if session.get("auth-token") :
        return redirect("/")

    if not allowCustomURLs :
        return redirect("/choose-city")

    return render_template("login.html", id="none")

@app.post("/login")
def loginHandler() :
    usr = request.form["usr"].strip()
    pswd = request.form["pswd"].strip()
    schoolID = request.form["id"].strip()

    try :
        url = request.form["url"].strip()
    except KeyError :
        url = "invalid"

    if not allowCustomURLs :
        schoolID = schoolID.split(";")

        try :
            city = schoolID[0]
            id = schoolID[1]

            url = schools.getSchoolURL(city, id)
        except :
            url = "invalid"

    if url == "invalid" :
        return redirect("/")

    url = url.strip("/")

    out = bakaapi.auth(url, usr, pswd)
    
    if out[0] == "error" :
        return "<h1>Invalid URL/Username/Password</h1> %s <br> <a href='/'>Go back</a>" % (out[1])
    
    refreshToken = out[1]
    userID = out[3]

    authToken = accounts.createAuthToken(userID)

    session["auth-token"] = authToken
    return redirect("/")

@app.get("/delete-cache")
def deleteCachePage() :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)
    basicInfo = accounts.getBasicInfoFromId(userID)

    url = basicInfo[0]
    refresh_token = basicInfo[1]

    userInfo = json.loads(bakaapi.getUserInfo(url, refresh_token, userID, False))

    return render_template("deleteCache.html", name=userInfo["FullName"])

@app.post("/delete-cache")
def deleteCache() :
    if not session.get("auth-token") :
        return redirect("/")
    
    authToken = session.get("auth-token")
    userID = accounts.getIdFromToken(authToken)

    accounts.deleteCache(userID)

    return redirect("/logout")

@app.get("/logout")
def logout() :
    accounts.invalidateToken(session.get("auth-token"))
    session["auth-token"] = None

    return redirect("/")

app.run(threaded=True, host="0.0.0.0", port=5000, debug=False)