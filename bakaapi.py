from pathlib import Path
import requests
import shelve
import json
import sys
import os

if not os.path.isdir("bakaAccounts") :
    os.mkdir("bakaAccounts")

def auth(url, username, password) :
    data = {
                "client_id": "ANDR",
                "grant_type": "password",
                "username": username,
                "password": password,
            }
    
    apiURL = url + "/api/login"

    try :
        r = requests.post(apiURL, data=data) # <--------
        j = json.loads(r.content.decode("utf-8"))

        s = shelve.open(str(Path("bakaAccounts/%s_basicinfo" % (j["bak:UserId"])))) #Using the normal shelve file jsut corrupted it for some reason. I spent almost 4 hours trying to debug it and failed
        s["refresh_token"] = j["refresh_token"]
        s["url"] = url
        s.close()

        return ["ok", j["refresh_token"], j["access_token"], j["bak:UserId"]]
    except Exception as e :
        try :
            return ["error", j["error_description"]]
        except :
            return ["error", e]

def refreshAccessToken(url, refresh_token) :
    data = {
                "client_id": "ANDR",
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
    
    url = url + "/api/login"

    try :
        r = requests.post(url, data=data)
        j = json.loads(r.content.decode("utf-8"))

        s = shelve.open(str(Path("bakaAccounts/%s_basicinfo" % (j["bak:UserId"]))))

        s["refresh_token"] = j["refresh_token"]

        s.sync()
        s.close()

        return ["ok", j["access_token"]]
    except Exception as e :
        print("ERROR! " + str(e))
        return ["error", e]

def requestAuthenticated(refresh_token, url, endpoint, data, method) :
    token = refreshAccessToken(url, refresh_token)[1]
    
    headers = {
             "Authorization": "Bearer %s" % (token)
            }
    
    url = url.strip("/")
    url = url + endpoint

    if method.lower() == "post" :
        r = requests.post(url, data=data, headers=headers)
    else :
        r = requests.get(url, data=data, headers=headers)
    return r.content

def getUserInfo(url, refresh_token, userID, forceRefresh) :
    s = shelve.open(str(Path("bakaAccounts/%s" % (userID))))

    try :
        if forceRefresh :
            raise KeyError
        userInfo = s["userInfo"]
    except KeyError :
        userInfo = requestAuthenticated(refresh_token, url, "/api/3/user", {}, "get").decode("utf-8")
        s["userInfo"] = userInfo
    
    s.close()
    return userInfo