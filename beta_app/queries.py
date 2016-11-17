import sqlite3
import hashlib
from time import time
from collections import OrderedDict
def connectDB():
    conn = sqlite3.connect("../nanna_radio.db")
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=True;")
    return (conn,cur)

def closeDB(conn):    
    conn.close()

def getUsers():
    (conn,cur) = connectDB()
    cur.execute("select user_id,username from UserProfile")
    data = cur.fetchall()
    closeDB(conn)
    return dict((y,x) for x,y in data)

def getProfile(user_id):
    (conn,cur) = connectDB()
    cur.execute("select username,first_name,last_name,strftime('%d-%m-%Y',date_of_birth),city, \
                 state from UserProfile where user_id=?",(user_id,))
    res = cur.fetchall()[0]
    data = OrderedDict()    
    #All the values are declared sequentially to store the order of values
    data['Email'] = res[0]
    data['First Name'] = res[1]
    data['Last Name'] = res[2]
    data['Date of Birth'] = res[3]
    data['City'] = res[4]
    data['State'] = res[5]
    if user_id in getActiveUsers():
        data['Active Status'] = True
    else:
        data['Active Status'] = False

    cur.execute("""select genre from FavouriteGenres as f JOIN UserProfile as u
                 where f.user_id = u.user_id""")

    tmp_fav = cur.fetchall()
    tmp_fav = [genre[0] for genre in tmp_fav]
    fav={}
    for each_genre in getGenres():
        if each_genre in tmp_fav:
            fav[each_genre] = True
        else:
            fav[each_genre] = False

    closeDB(conn)
    return (data,fav)

def insertProfile(username, first, last, dob, city, state, passwd):
    (conn,cur) = connectDB()
    user_id = int(time())
    md5 = hashlib.md5()
    md5.update(passwd)
    hash_pass = md5.hexdigest()

    try:
        cur.execute("insert into UserProfile values (?,?,?,?,?,?,?,?)"
                    ,(user_id,username,first,last,dob,city,state,None))
        cur.execute("insert into Credentials values \
                    (?,?,?)",(user_id,username,hash_pass))
        conn.commit()
    except Exception as e:
        print e
        conn.rollback()
        return False
    finally:        
        closeDB(conn)
    return True

def updateProfile(user_id,data):
    (conn,cur) = connectDB()
    first = data['first']
    last = data['last']
    genreCount = data['genreCount']

    try:
        cur.execute("update UserProfile set first_name=? where user_id=?",(first,user_id))
        cur.execute("update UserProfile set last_name=? where user_id=?",(last,user_id))        
        allGenres = getGenres()
        userGenres=[]
        for i in range(len(allGenres)):
            try:
                userGenres.append(data['genre'+str(i)])
            except Exception as e:
                print "Error in ",e
        print "userGenres = ",userGenres
        for each_genre in allGenres:
            if each_genre in userGenres:
                cur.execute("insert or replace into FavouriteGenres values(?,?)",(user_id,each_genre))
                print "Insert ",each_genre
            else:
                cur.execute("delete from FavouriteGenres where user_id=? and genre=?",(user_id,each_genre))
                print "Delete ",each_genre
        conn.commit()
    except Exception as e:
        print "Error in updateProfile query : ",e
        conn.rollback()
        raise e
    finally:
        closeDB(conn)

def checkLogin(username,password):
    (conn,cur) = connectDB()
    md5 = hashlib.md5()
    md5.update(password)
    hash_pass = md5.hexdigest()
    cur.execute("select md5_passwd,user_id from Credentials\
     where username=?",(username,))
    res = cur.fetchall()
    cur.execute("select first_name from UserProfile where user_id=?",(res[0][1],))
    first = cur.fetchall()[0][0]
    #print "Generated: ",res[0][0],"Required",hash_pass
    closeDB(conn)
    try:
        if res[0][0] == hash_pass:
            #md5 match
            print "Password Matched"
            return (res[0][1],username,first)
        else:
            return None
    except Exception as e:
        print # coding=utf-8
        return None

def createToken(user_id):
    print "createToken"
    (conn,cur) = connectDB()
    salt = unicode(int(time())) + "ssaalltt"
    md5 = hashlib.md5()
    md5.update(str(user_id) + salt)
    token = md5.hexdigest()
    try:
        cur.execute("INSERT or REPLACE INTO LoggedInUsers values(?,?)",(user_id,token))
        conn.commit()
    except Exception as e:
        print "Error in createToken",e
        conn.rollback()
        closeDB(conn)
        return False

    closeDB(conn)
    return token

def getLoggedinUsers():
    (conn,cur) = connectDB()
    cur.execute("select user_id,token from LoggedInUsers")
    users = cur.fetchall()
    users = dict((x,y) for x,y in users)
    closeDB(conn)
    return users

def logoutUser(user_id,token):
    (conn,cur) = connectDB()
    cur.execute("delete from LoggedInUsers where user_id=? and token=?",(user_id,token))
    conn.commit()
    closeDB(conn)
    return True

# Queries related to songs
def getSongs(min,max):
    (conn,cur) = connectDB()
    cur.execute("select name,url,img_url from Songs LIMIT ?,?",(min-1,max-min))
    songslist = cur.fetchall()
    cur.execute("select count(song_id) from Songs");
    songsCount = cur.fetchall()[0][0]
    
    closeDB(conn)
    return (songslist,songsCount)

def getGenres():
    return ['Classical','Patriotic','Devotional','Mild']

# Active users are defined as -> last_logged_in time within 1 week
def getActiveUsers():
    (conn,cur) = connectDB()
    cur.execute("""select user_id from UserProfile where
     ((strftime("%s","now")-strftime("%s",last_logged_in))/3600)<(24*7)""")
    data = cur.fetchall()
    data = [val[0] for val in data]
    closeDB(conn)
    return data      