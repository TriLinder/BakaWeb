from pathlib import Path
import shelve
import random
import os

abc = "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z"
abc = abc + "," + abc.upper()
abc = abc.split(",")

if not os.path.isdir("db") :
    os.mkdir("db")

def genAuthToken(lenght) :
    token = ""

    for i in range(lenght) :
        token = token + random.choice(abc)


    return token

def createAuthToken(userid) :
    token = genAuthToken(32)

    s = shelve.open(str(Path("db/authTokens")))
    s[token] = userid
    s.close()

    return token

def getIdFromToken(token) :
    s = shelve.open(str(Path("db/authTokens")))

    try :
        out = s[token]
    except :
        out =  False
    
    s.close()
    return out

def getBasicInfoFromId(id) :
    s = shelve.open(str(Path("bakaAccounts/%s_basicinfo" % (id))), flag="r")

    refresh_token = s["refresh_token"]
    url = s["url"]

    s.close()

    return [url, refresh_token]

def invalidateToken(token) :
    if getIdFromToken(token) :
        s = shelve.open(str(Path("db/authTokens")))
        s[token] = None
        s.close()

        return True
    else :
        return False

def deleteCache(userID) :
    s = shelve.open(str(Path("bakaAccounts/%s" % (userID))), flag="n")
    s.close()

    s = shelve.open(str(Path("bakaAccounts/%s_basicinfo" % (userID))), flag="n")
    s.close()