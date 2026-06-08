from flask import g, request, jsonify
import sqlite3

def connect_db():
    sql = sqlite3.connect('./database.db')
    sql.row_factory = sqlite3.Row
    return sql

def get_db():
    if not hasattr(g, 'sqlite3'):
        g.sqlite3_db = connect_db()
    return g.sqlite3_db

def loadTeamInfo(name, abbrv, conf, div, logo):
    db = get_db()
    db.execute('INSERT INTO teams (name,abbrv,conf,div,logo) VALUES (?,?,?,?,?)', [name, abbrv, conf, div, logo])
    db.commit()
    return

def dataEmpty(table):
    db = get_db()
    cursor = db.execute('select * from '+table)
    results = cursor.fetchall()
    if len(results) == 0:
        return True
    else:
        return False
    
teams = ['Arizona Cardinals','Atlanta Falcons','Baltimore Ravens','Buffalo Bills','Carolina Panthers','Chicago Bears','Cincinnati Bengals','Cleveland Browns','Dallas Cowboys',
         'Denver Broncos','Detroit Lions','Green Bay Packers','Houston Texans','Indianapolis Colts','Jacksonville Jaguars','Kansas City Chiefs','Las Vegas Raiders','Los Angeles Chargers',
         'Los Angeles Rams','Miami Dolphins','Minnesota Vikings','New England Patriots','New Orleans Saints','New York Giants','New York Jets','Philadelphia Eagles','Pittsburgh Steelers',
         'San Francisco 49ers','Seattle Seahawks','Tampa Bay Buccaneers','Tennessee Titans','Washington Commanders']
abbrv = ['ARI','ATL','BAL','BUF','CAR','CHI','CIN','CLE','DAL','DEN','DET','GB','HOU','IND','JAX','KC','MIA','MIN','NE','NO','NYG','NYJ','LV','PHI','PIT','LAC','SF','SEA','LAR','TB','TEN','WAS']
conf = ['NFC','NFC','AFC','AFC','NFC','NFC','AFC','AFC','NFC','AFC','NFC','NFC','AFC','AFC','AFC','AFC','AFC','NFC','AFC','NFC','NFC','AFC','AFC','NFC','AFC','AFC','NFC','NFC','NFC','NFC','AFC',
        'NFC']
div = ['West','South','North','East','South','North','North','North','East','West','North','North','South','South','South','West','East','North','East','South','East','East','West','East',
       'North','West','West','West','West','South','South','East']
    
if dataEmpty(table='teams'):
    for i in range(0,len(teams)):
        loadTeamInfo(teams[i],abbrv[i],conf[i],div[i],'logos/'+teams[i].replace(' ','')+'.png')
    print ('Database Loaded')
else:
    print ('Database already contains data')