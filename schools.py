from collections import OrderedDict
from bs4 import BeautifulSoup
from pathlib import Path
import urllib.parse
import requests
import shelve
import time
import os

if not os.path.isdir("db") :
    os.mkdir("db")

def getCities() :
    s = shelve.open(str(Path("db/schools")))

    try :
        cities = s["list"]
        
        if time.time() - s["list_lastUpdate"] > (30*24*60*60) :
            raise KeyError
    except KeyError :
        r = requests.get("https://sluzby.bakalari.cz/api/v1/municipality/")

        xmlData = r.content.decode("utf-8")

        bs_data = BeautifulSoup(xmlData, 'xml')

        cities = []

        for city in bs_data.find_all('name') :
            cities.append(str(city).split(">")[1].split("<")[0])
        
        s["list"] = OrderedDict.fromkeys(cities)
        s["list_lastUpdate"] = round(time.time())

        s.close()
    
    return cities

def getSchools(search) :
    if not search in getCities() :
        return "invalidCity"

    s = shelve.open(str(Path("db/schools")))

    try :
        schools = s["search_" + search]
        
        if time.time() - s["searchL_" + search] > (14*24*60*60) :
            raise KeyError

    except KeyError :
        r = requests.get("https://sluzby.bakalari.cz/api/v1/municipality/%s" % (urllib.parse.quote_plus(search.split(".")[0])))

        xmlData = r.content.decode("utf-8")

        bs_data = BeautifulSoup(xmlData, 'xml')

        schools = []

        for school in bs_data.find_all('schoolInfo') :
            name = str(school).split("<name>")[1].split("</name>")[0]
            url = str(school).split("<schoolUrl>")[1].split("</schoolUrl>")[0]
            search = search
            id = str(school).split("<id>")[1].split("</id>")[0]

            schools.append({"name":name, "url":url, "search":search, "id":id})
        
        s["search_" + search] = schools
        s["searchL_" + search] = round(time.time())

        s.close()
    
    return schools

def chooseCityHtml(cities) :
    html = ""

    for city in cities :
        html = html + "<a href='/city/%s'>%s</a> <br>" % (city, city)

    return html

def chooseSchoolHtml(schools) :
    html = ""

    for school in schools :
        html = html + "<a href='/login-school/%s/%s'>%s</a> <br>" % (school["search"], school["id"], school["name"])
    
    return html

def getSchoolURL(city, id) :
    schools = getSchools(city)

    if schools == "invalidCity" :
        return "invalid"

    for school in schools :
        if school["id"] == id :
            return school["url"]
    
    return "invalid"