import sqlite3
import time
from datetime import date

import pandas as pd
import sqlalchemy as SQLA
from flask import g
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

teams = [
    "Arizona Cardinals",
    "Atlanta Falcons",
    "Baltimore Ravens",
    "Buffalo Bills",
    "Carolina Panthers",
    "Chicago Bears",
    "Cincinnati Bengals",
    "Cleveland Browns",
    "Dallas Cowboys",
    "Denver Broncos",
    "Detroit Lions",
    "Green Bay Packers",
    "Houston Texans",
    "Indianapolis Colts",
    "Jacksonville Jaguars",
    "Kansas City Chiefs",
    "Las Vegas Raiders",
    "Los Angeles Chargers",
    "Los Angeles Rams",
    "Miami Dolphins",
    "Minnesota Vikings",
    "New England Patriots",
    "New Orleans Saints",
    "New York Giants",
    "New York Jets",
    "Philadelphia Eagles",
    "Pittsburgh Steelers",
    "San Francisco 49ers",
    "Seattle Seahawks",
    "Tampa Bay Buccaneers",
    "Tennessee Titans",
    "Washington Commanders",
]
abbrv = [
    "ARI",
    "ATL",
    "BAL",
    "BUF",
    "CAR",
    "CHI",
    "CIN",
    "CLE",
    "DAL",
    "DEN",
    "DET",
    "GB",
    "HOU",
    "IND",
    "JAX",
    "KC",
    "LV",
    "LAC",
    "LAR",
    "MIA",
    "MIN",
    "NE",
    "NO",
    "NYG",
    "NYJ",
    "PHI",
    "PIT",
    "SF",
    "SEA",
    "TB",
    "TEN",
    "WAS",
]
conf = [
    "NFC",
    "NFC",
    "AFC",
    "AFC",
    "NFC",
    "NFC",
    "AFC",
    "AFC",
    "NFC",
    "AFC",
    "NFC",
    "NFC",
    "AFC",
    "AFC",
    "AFC",
    "AFC",
    "AFC",
    "AFC",
    "NFC",
    "AFC",
    "NFC",
    "AFC",
    "NFC",
    "NFC",
    "AFC",
    "NFC",
    "AFC",
    "NFC",
    "NFC",
    "NFC",
    "AFC",
    "NFC",
]
div = [
    "West",
    "South",
    "North",
    "East",
    "South",
    "North",
    "North",
    "North",
    "East",
    "West",
    "North",
    "North",
    "South",
    "South",
    "South",
    "West",
    "West",
    "West",
    "West",
    "East",
    "North",
    "East",
    "South",
    "East",
    "East",
    "East",
    "North",
    "West",
    "West",
    "South",
    "South",
    "East",
]


def createTeamDict():
    teamDict = []
    db = get_db("databasecopy.db")
    cursor = db.execute("select id, name, abbrv, conf, div, logo from teams")
    results = cursor.fetchall()
    cursor.close()
    for result in results:
        teamDict.append(
            {
                "id": result["id"],
                "name": result["name"],
                "abbrv": result["abbrv"],
                "conf": result["conf"],
                "div": result["div"],
                "logo": result["logo"],
                "display": False,
            }
        )
    db.close()
    return teamDict


def connect_db(location):
    sql = sqlite3.connect("./" + location)
    sql.row_factory = sqlite3.Row
    return sql


def get_db(location):
    if not hasattr(g, "sqlite3"):
        g.sqlite3_db = connect_db(location)
    return g.sqlite3_db


def get_all(dbname, table):
    db = get_db(dbname)
    cursor = db.execute("select * from " + table)
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return results


def getPlayers():
    db = get_db("databasecopy.db")
    cursor = db.execute("SELECT * from players")
    players = cursor.fetchall()
    cursor.close()
    db.close()
    return players


def archiveRanks(data, ranks):
    dbname = data["data"] + str(data["year"])
    engine = SQLA.create_engine("sqlite:///projectionscopy.db")
    inspect = SQLA.inspect(engine)
    if not inspect.has_table(dbname):
        ranksdf = pd.DataFrame(ranks)
        if data["data"] == "espnproj":
            ranksdf = ranksdf[[0, 1, 14]]
        else:
            ranksdf = ranksdf[[0, 1, 2]]

        ranksdf.to_sql(dbname, engine, index=False)
        clean = True

    else:
        print("Archived Data Exists!")
        clean = False

    return clean


def loadProjections():
    db = get_db("databasecopy.db")
    cursor = db.execute("Select * from espnproj")
    espnproj = cursor.fetchall()
    cursor.close()
    if len(espnproj) == 0:
        url = "https://fantasy.espn.com/football/players/projections"
        listPlayers = []
        driver = webdriver.Firefox()
        driver.maximize_window()
        driver.get(url)
        x = 0
        rankAdjust = 0
        while x < 6:
            time.sleep(5)
            players = driver.find_elements(
                By.CLASS_NAME, "jsx-2175038926.player-info-section.flex"
            )
            for player in players:
                playerDict = {}
                playerDict["name"] = player.find_element(
                    By.CLASS_NAME, "AnchorLink.link.clr-link.pointer"
                ).text
                if playerDict["name"].split(" ")[1] == "D/ST":
                    playerDict["pos"] = "D/ST"
                else:
                    playerDict["pos"] = player.find_element(
                        By.CLASS_NAME, "position-eligibility"
                    ).text
                if playerDict["pos"] not in ["K", "D/ST"]:
                    playerDict["rank"] = (
                        int(
                            player.find_element(
                                By.CLASS_NAME, "playerInfo__rank.Table__TD"
                            ).text
                        )
                        - rankAdjust
                    )
                    table = player.find_element(
                        By.CLASS_NAME, "jsx-2175038926.stat-info-section"
                    )
                    tableproj = table.find_elements(
                        By.CLASS_NAME, "Table__TR.Table__TR--sm.Table__odd"
                    )
                    proj = tableproj[1].find_elements(By.CLASS_NAME, "Table__TD")
                    if playerDict["pos"] in ["WR", "TE"]:
                        playerDict["tar"] = proj[1].text
                        playerDict["rec"] = proj[2].text
                        playerDict["recyds"] = proj[3].text
                        playerDict["rectds"] = proj[5].text
                        playerDict["rushatt"] = proj[6].text
                        playerDict["rushyds"] = proj[7].text
                        playerDict["rushtds"] = proj[8].text
                        playerDict["pts"] = proj[9].text
                    elif playerDict["pos"] == "RB":
                        playerDict["rushatt"] = proj[1].text
                        playerDict["rushyds"] = proj[2].text
                        playerDict["rushtds"] = proj[4].text
                        playerDict["rec"] = proj[5].text
                        playerDict["recyds"] = proj[6].text
                        playerDict["rectds"] = proj[7].text
                        playerDict["pts"] = proj[8].text
                    elif playerDict["pos"] == "QB":
                        playerDict["c/a"] = proj[1].text
                        playerDict["passyds"] = proj[2].text
                        playerDict["passtds"] = proj[3].text
                        playerDict["int"] = proj[4].text
                        playerDict["rushatt"] = proj[5].text
                        playerDict["rushyds"] = proj[6].text
                        playerDict["rushtds"] = proj[7].text
                        playerDict["pts"] = proj[8].text
                    listPlayers.append(playerDict)
                else:
                    rankAdjust = rankAdjust + 1
            driver.find_element(
                By.XPATH,
                '//*[@id="fitt-analytics"]/div/div[5]/div[2]/div[3]/div/div/div/div/nav/button[2]',
            ).click()
            x = x + 1
        driver.close()
        x = 0
        while x < len(listPlayers):
            names = listPlayers[x]["name"].split(" ")
            full = "%" + names[0] + " " + names[1] + "%"
            last = "%" + names[1] + "%"
            initial = names[0][:1] + "%"
            cursor = db.execute(
                "select * from players where name like ? and pos = ?",
                [full, listPlayers[x]["pos"]],
            )
            database = cursor.fetchone()
            y = 0
            posRank = 1
            while y < x:
                if listPlayers[y]["pos"] == listPlayers[x]["pos"]:
                    posRank = posRank + 1
                y = y + 1
            posrank = listPlayers[x]["pos"] + str(posRank)
            if database == None:
                print(listPlayers[x]["name"])
            else:
                if listPlayers[x]["pos"] == "QB":
                    data = [
                        listPlayers[x]["rank"],
                        database["id"],
                        listPlayers[x]["rushatt"],
                        listPlayers[x]["rushyds"],
                        listPlayers[x]["rushtds"],
                        listPlayers[x]["c/a"],
                        listPlayers[x]["passyds"],
                        listPlayers[x]["passtds"],
                        listPlayers[x]["int"],
                        listPlayers[x]["pts"],
                        posrank,
                    ]
                    db.execute(
                        "insert into espnproj (rank, playerid, car, rushyds, rushtd, compperatt, yds, passtd, interceptions, fpts, posrank) values (?,?,?,?,?,?,?,?,?,?,?)",
                        data,
                    )
                elif listPlayers[x]["pos"] in ["WR", "TE"]:
                    data = [
                        listPlayers[x]["rank"],
                        database["id"],
                        listPlayers[x]["rushatt"],
                        listPlayers[x]["rushyds"],
                        listPlayers[x]["rushtds"],
                        listPlayers[x]["tar"],
                        listPlayers[x]["rec"],
                        listPlayers[x]["recyds"],
                        listPlayers[x]["rectds"],
                        listPlayers[x]["pts"],
                        posrank,
                    ]
                    db.execute(
                        "insert into espnproj (rank, playerid, car, rushyds, rushtd, tar, rec, recyds, rectds, fpts, posrank) values (?,?,?,?,?,?,?,?,?,?,?)",
                        data,
                    )
                else:
                    data = [
                        listPlayers[x]["rank"],
                        database["id"],
                        listPlayers[x]["rushatt"],
                        listPlayers[x]["rushyds"],
                        listPlayers[x]["rushtds"],
                        listPlayers[x]["rec"],
                        listPlayers[x]["recyds"],
                        listPlayers[x]["rectds"],
                        listPlayers[x]["pts"],
                        posrank,
                    ]
                    db.execute(
                        "insert into espnproj (rank, playerid, car, rushyds, rushtd, rec, recyds, rectds, fpts, posrank) values (?,?,?,?,?,?,?,?,?,?)",
                        data,
                    )
            db.commit()
            x = x + 1
        print("ESPN Projections Loaded.")
    else:
        print("ESPN Projections Exist.")
    cursor = db.execute("Select * from FPranks")
    result = cursor.fetchall()
    cursor.close()
    if len(result) == 0:
        url = "https://www.fantasypros.com/nfl/rankings/ppr-cheatsheets.php"
        listPlayers = []
        driver = webdriver.Firefox()
        driver.maximize_window()
        driver.get(url)
        rankAdjust = 0
        time.sleep(5)
        players = driver.find_elements(By.CLASS_NAME, "player-row")
        for player in players:
            playerData = {}
            playerData["rank"] = int(
                player.find_element(By.CLASS_NAME, "sticky-cell.sticky-cell-one").text
            )
            playerCell = player.find_element(
                By.CLASS_NAME, "player-cell.player-cell__td"
            )
            playerData["name"] = playerCell.find_element(By.CSS_SELECTOR, "a").text
            posRank = player.find_elements(By.CSS_SELECTOR, "td")[3].text
            x = 0
            while x < len(posRank):
                try:
                    rankPos = int(posRank[x:])
                except ValueError as e:
                    x = x + 1
                else:
                    playerData["posRank"] = posRank
                    playerData["pos"] = posRank[0:x]
                    x = 100
            if player.find_element(By.CLASS_NAME, "player-cell-team").text != "(FA)":
                playerData["SOS"] = player.find_element(By.CLASS_NAME, "sr-only").text
            else:
                playerData["SOS"] = ""
            listPlayers.append(playerData)
        driver.close()
        adjustRank = 0
        x = 0
        while x < 408:
            if listPlayers[x]["pos"] in ["K", "DST"]:
                adjustRank = adjustRank + 1
            else:
                cursor = db.execute(
                    "Select * from players where name = ?", [listPlayers[x]["name"]]
                )
                database = cursor.fetchone()
                if database == None:
                    splitName = listPlayers[x]["name"].split(" ")
                    cursor = db.execute(
                        "select * from players where name = ?",
                        [splitName[0] + " " + splitName[1]],
                    )
                    database = cursor.fetchone()
                    if database != None:
                        data = [
                            (listPlayers[x]["rank"] - adjustRank),
                            database["id"],
                            listPlayers[x]["posRank"],
                            listPlayers[x]["SOS"],
                        ]
                        db.execute(
                            "insert into FPranks (rank, playerid, posrank, SOS) values (?,?,?,?)",
                            data,
                        )
                else:
                    data = [
                        (listPlayers[x]["rank"] - adjustRank),
                        database["id"],
                        listPlayers[x]["posRank"],
                        listPlayers[x]["SOS"],
                    ]
                    db.execute(
                        "insert into FPranks (rank, playerid, posrank, SOS) values (?,?,?,?)",
                        data,
                    )
            x = x + 1
        db.commit()
        print("FP Projections Loaded.")
        cursor = db.execute("Select * from FPranks")
        result = cursor.fetchall()
        cursor.close()
    else:
        print("FP Projections Exist.")
    cursor = db.execute("Select * from CBSranks")
    result = cursor.fetchall()
    cursor.close()
    if len(result) == 0:
        url = "https://www.cbssports.com/fantasy/football/rankings/ppr/top200/"
        listPlayers = []
        driver = webdriver.Firefox()
        driver.maximize_window()
        driver.get(url)
        time.sleep(5)
        consensus = driver.find_element(By.CLASS_NAME, "player-wrapper")
        players = consensus.find_elements(By.CLASS_NAME, "player-row")
        for player in players:
            playerData = {}
            playerData["rank"] = player.find_element(By.CLASS_NAME, "rank").text
            playerData["name"] = player.find_element(By.CSS_SELECTOR, "a").text
            playerData["pos"] = player.find_element(
                By.CLASS_NAME, "team.position"
            ).text.split(" ")[0]
            playerData["team"] = player.find_element(
                By.CLASS_NAME, "team.position"
            ).text.split(" ")[0]
            listPlayers.append(playerData)
        x = 0
        while x < len(listPlayers):
            y = 0
            posRank = 1
            while y < x:
                if listPlayers[x]["pos"] == listPlayers[y]["pos"]:
                    posRank = posRank + 1
                y = y + 1
            listPlayers[x]["posRank"] = listPlayers[x]["pos"] + str(posRank)
            x = x + 1

        for player in listPlayers:
            if player["name"] == "N. Dell":
                player["name"] = "T. Dell"
            player["found"] = False
            if player["team"] == "JAC":
                player["team"] = "JAX"
            names = player["name"].split(". ")
            last = "%" + names[1] + "%"
            initial = names[0] + "%"
            cursor = db.execute(
                "select * from players where pos = ? and name like ? and name like ? and teamid != ?",
                [player['pos'],initial, last, 33],
            )
            result = cursor.fetchall()
            cursor.close()
            if len(result) != 0:
                if len(result) > 1:
                    match=[]
                    for option in result:
                        cursor = db.execute('select * from espnproj where playerid = ?',[option['id']])
                        espnrank = cursor.fetchall()
                        cursor.close()
                        if len(espnrank)==1:
                            match.append(espnrank[0]['rank']-int(player['rank']))
                        elif len(espnrank)>1:
                            print(option['id'])
                        else:
                            match.append(False)
                            
                    
                    min= 0
                    if player['name'] =='A. St. Brown':
                        player['id']=315
                        player['found']=True
                    elif player['name'] =='D. Samuel':
                        player['found']=True
                        player['id']=822                        
                        
                else:
                    player['id']=result[0]['id']
                    player['found']=True
                            
            if player["found"] == False:
                print(player["name"])
            else:
                db.execute(
                    "insert into CBSranks (rank, playerid, posrank) values (?,?,?)",
                    [player["rank"], player["id"], player["posRank"]],
                )

        db.commit()
        driver.close()
        print("CBS Ranks Loaded!")
    else:
        print("CBS Ranks Exist.")
    loadAvgRanks()
    db.close()
    return


def loadAvgRanks():
    db = get_db("databasecopy.db")
    cursor = db.execute("select * from avgranks")
    result = cursor.fetchall()
    cursor.close()
    if len(result) < 1:
        players = getPlayers()
        avgranks = []
        for player in players:
            data = {"id": player["id"], "avg": None}
            data["ranks"] = []
            data["team"] = player["teamid"]
            data["SOS"] = ""
            cursor = db.execute(
                "select * from espnproj where playerid = ?", [player["id"]]
            )
            result = cursor.fetchone()
            if result != None:
                data["ranks"].append(result["rank"])
            cursor = db.execute(
                "select * from CBSranks where playerid = ?", [player["id"]]
            )
            result = cursor.fetchone()
            if result != None:
                data["ranks"].append(result["rank"])
            cursor = db.execute(
                "select * from FPranks where playerid = ?", [player["id"]]
            )
            result = cursor.fetchone()
            if result != None:
                data["ranks"].append(result["rank"])
                data["SOS"] = result["SOS"]
            data["ranks"].sort()
            data["pos"] = player["pos"]
            divisor = 0
            total = 0
            for rank in data["ranks"]:
                divisor = divisor + 1
                total = total + rank
            if total != 0:
                avg = total / divisor
                data["avg"] = avg
                avgranks.append(data)
        sorted = []

        while len(avgranks) > 1:
            lowest = None
            x = 0
            while x < len(avgranks):
                if lowest == None:
                    lowest = x
                else:
                    if avgranks[x]["avg"] == avgranks[lowest]["avg"]:
                        if avgranks[x]["ranks"][0] < avgranks[lowest]["ranks"][0]:
                            lowest = x
                    elif avgranks[x]["avg"] < avgranks[lowest]["avg"]:
                        lowest = x
                x = x + 1
            sorted.append(avgranks[lowest])
            avgranks.remove(avgranks[lowest])
        sorted = sorted + avgranks
        x = 0
        while x < len(sorted):
            posrank = 1
            y = 0
            while y < x:
                if sorted[y]["pos"] == sorted[x]["pos"]:
                    posrank = posrank + 1
                y = y + 1
            sorted[x]["posrank"] = sorted[x]["pos"] + str(posrank)
            x = x + 1
        for item in sorted:
            if item["SOS"] == "" and item["team"] != 33:
                for sos in sorted:
                    if (
                        item["pos"] == sos["pos"]
                        and item["team"] == sos["team"]
                        and sos["SOS"] != ""
                    ):
                        item["SOS"] = sos["SOS"]
        x = 0
        while x < len(sorted):
            if sorted[x]["SOS"] != "":
                db.execute(
                    "insert into avgranks (rank,playerid,posrank,SOS) values (?,?,?,?)",
                    [x + 1, sorted[x]["id"], sorted[x]["posrank"], sorted[x]["SOS"]],
                )
            else:
                db.execute(
                    "insert into avgranks (rank,playerid,posrank) values (?,?,?)",
                    [x + 1, sorted[x]["id"], sorted[x]["posrank"]],
                )
            x = x + 1
        db.commit()
        print("AVG Ranks Loaded!")
    else:
        print("AVG Ranks Exist.")
    db.close()
    return


def autoData():
    db = get_db("databasecopy.db")
    cursor = db.execute("select * from edit")
    results = cursor.fetchall()
    cursor.close()
    today = date.today()
    for data in results:
        if data["data"] == "rosters":
            if today.month > 4 and (
                data["month"] < today.month or data["year"] < today.year
            ):
                loadRosters()
                db.execute(
                    "update edit set month = ?,day = ?, year = ? where data = 'rosters'",
                    [today.month, today.day, today.year],
                )
                db.commit()
    corruptDb=False
    for data in results:
        if data["data"] in ["espnproj", "CBSranks", "FPranks", "avgranks"]:
            if today.month >= 9 or today.year > data["year"]:
                ranks = get_all(data["location"], data["data"])
                if archiveRanks(data, ranks):
                    db.execute("delete from " + data["data"])
                    values = [
                        data["data"] + str(data["year"]),
                        "false",
                        data["month"],
                        data["day"],
                        data["year"],
                        "projectionscopy.db",
                    ]
                    db.execute(
                        "insert into edit (data,edit,month,day,year,location) values (?,?,?,?,?,?)",
                        values,
                    )
                    print(data["data"] + " cleared.")
                elif today.month > 4 and (
                    today.month > data["month"] or today.day - data["day"] > 7
                ):
                    db.execute("delete from " + data["data"])
                    values = [today.month, today.day, today.year, data["data"]]
                    db.execute(
                        "update edit set month = ?, day = ?, year = ? where data = ?",
                        values,
                    )
    db.commit()
    db.close()
    if today.month > 4 and today.month < 9:
        loadProjections()
    return


def addPlayer(player):
    db = get_db("databasecopy.db")
    db.execute(
        "INSERT INTO players (teamid, name, num, pos, age, exp, photo) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            player["teamid"],
            player["name"],
            player["num"],
            player["pos"],
            player["age"],
            player["exp"],
            player["photo"],
        ],
    )
    db.commit()
    db.close()
    return


def addPlayercopy(player):
    db = get_db("databasecopy.db")
    if player["num"] != None:
        db.execute(
            "INSERT INTO players (teamid, name, num, pos, age, exp, photo) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                player["teamid"],
                player["name"],
                player["num"],
                player["pos"],
                player["age"],
                player["exp"],
                player["photo"],
            ],
        )
    else:
        db.execute(
            "INSERT INTO players (teamid, name, pos, age, exp, photo) VALUES (?, ?, ?, ?, ?, ?)",
            [
                player["teamid"],
                player["name"],
                player["pos"],
                player["age"],
                player["exp"],
                player["photo"],
            ],
        )
    db.commit()
    db.close()
    return


def loadTeamInfo():

    engine = SQLA.create_engine("sqlite:///databasecopy.db")

    if (
        engine.dialect.has_table(table_name="teams", connection=engine.connect())
        == False
    ):
        db = get_db("databasecopy.db")
        for i in range(0, len(teams)):
            db.execute(
                "INSERT INTO teams (name,abbrv,conf,div,logo) VALUES (?,?,?,?,?)",
                [teams[i], abbrv[i], conf[i], div[i], "logos/" + abbrv[i] + ".webp"],
            )
        db.commit()
        db.close()
        print("Team data loaded.")
    else:
        print("Team data already exists.")

    return


def getPlayerStats(team, year):
    db = get_db("databasecopy.db")
    cursor = db.execute("SELECT * from teams where name = ?", [team])
    org = cursor.fetchone()
    cursor = db.execute(
        "SELECT * from passing where teamid = ? and year = ?", [org["id"], int(year)]
    )
    passing = cursor.fetchall()
    cursor = db.execute(
        "SELECT * from rushing where teamid = ? and year = ?", [org["id"], int(year)]
    )
    rushing = cursor.fetchall()
    cursor = db.execute(
        "SELECT * from recieving where team = ? and year = ?", [org["id"], int(year)]
    )
    receiving = cursor.fetchall()
    passers = []
    for passer in passing:
        cursor = db.execute("SELECT * from players where id = ?", [passer["playerid"]])
        result = cursor.fetchone()
        passers.append(
            {
                "id": result["id"],
                "name": result["name"],
                "pos": result["pos"],
                "keys": passer.keys(),
                "stats": passer,
            }
        )
    rushers = []
    for rusher in rushing:
        cursor = db.execute("SELECT * from players where id = ?", [rusher["playerid"]])
        result = cursor.fetchone()
        rushers.append(
            {
                "id": result["id"],
                "name": result["name"],
                "pos": result["pos"],
                "keys": rusher.keys(),
                "stats": rusher,
            }
        )
    recievers = []
    for reciever in receiving:
        cursor = db.execute(
            "SELECT * from players where id = ?", [reciever["playerid"]]
        )
        result = cursor.fetchone()
        recievers.append(
            {
                "id": result["id"],
                "name": result["name"],
                "pos": result["pos"],
                "keys": reciever.keys(),
                "stats": reciever,
            }
        )

    return [passers, rushers, recievers]


def getPlayer(id):
    db = get_db("databasecopy.db")
    cursor = db.execute("select * from players where id = ?", [id])
    player = cursor.fetchone()
    cursor.close()
    db.close()
    return player


def grabRanks():
    db = get_db("databasecopy.db")
    cursor = db.execute("select * from espnproj")
    espnproj = cursor.fetchall()
    cursor.close()
    cursor = db.execute("select * from FPranks")
    FPranks = cursor.fetchall()
    cursor.close()
    cursor = db.execute("select * from CBSranks")
    CBSranks = cursor.fetchall()
    cursor.close()
    cursor = db.execute("select * from avgranks")
    avgranks = cursor.fetchall()
    cursor.close()
    return [espnproj, FPranks, CBSranks, avgranks]


def getTeam(id):
    db = get_db("databasecopy.db")
    cursor = db.execute("select * from teams where id = ?", [id])
    team = cursor.fetchone()
    cursor.close()
    db.close()
    return team


def grabPlayerData(players):
    db = get_db("databasecopy.db")
    playerdata = []
    for player in players:
        player = player
        cursor = db.execute("SELECT * from players where id = ?", [player])
        playerInfo = cursor.fetchone()
        cursor = db.execute("SELECT * from passing where playerid = ?", [player])
        passing = cursor.fetchall()
        cursor = db.execute("SELECT * from rushing where playerid = ?", [player])
        rushing = cursor.fetchall()
        cursor = db.execute("SELECT * from recieving where playerid = ?", [player])
        recieving = cursor.fetchall()
        cursor = db.execute("SELECT * from fantasy where playerid = ?", [player])
        fantasySeasons = cursor.fetchall()
        fantasy = []
        for season in fantasySeasons:
            info = {}
            info["rank"] = season["rank"]
            info["year"] = int(season["year"])
            info["avg"] = season["avg"]
            info["tot"] = season["total"]
            info["weeks"] = season["weeks"].split(" ")
            fantasy.append(info)

        playerdata.append(
            {
                "player": playerInfo,
                "passing": passing,
                "rushing": rushing,
                "recieving": recieving,
                "fantasy": fantasy,
            }
        )
    cursor.close()
    db.close()
    return playerdata


def getFantasyStats(year):
    db = get_db("databasecopy.db")
    cursor = db.execute("SELECT * from fantasy where year = ?", [year])
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result


def getFantasyPageStats(year, position):
    fantasy = getFantasyStats(year)
    db = get_db("databasecopy.db")
    cursor = db.execute("SELECT * from fantasy where year = ?", [year])
    stats = cursor.fetchall()
    cursor.close()
    players = []

    if position != "Select Position":
        for stat in stats:
            recieving = False
            cursor = db.execute(
                "SELECT * from players where id = ?", [stat["playerid"]]
            )
            player = cursor.fetchone()
            cursor.close()

            if player["pos"] == position:
                cursor = db.execute(
                    "select * from passing where playerid = ? and year = ?",
                    [player["id"], year],
                )
                result = cursor.fetchone()
                cursor.close()
                if result != None:
                    oldTeam = result["teamid"]
                cursor = db.execute(
                    "select * from rushing where playerid = ? and year = ?",
                    [player["id"], year],
                )
                result = cursor.fetchone()
                cursor.close()
                if result != None:
                    oldTeam = result["teamid"]
                cursor = db.execute(
                    "select * from recieving where playerid = ? and year = ?",
                    [player["id"], year],
                )
                result = cursor.fetchone()
                cursor.close()
                if result != None:
                    oldTeam = result["team"]
                    recieving = True

                players.append(
                    {
                        "rank": stat["rank"],
                        "name": player["name"],
                        "pos": player["pos"],
                        "team": player["teamid"],
                        "oldteam": oldTeam,
                        "weeks": stat["weeks"],
                        "avg": stat["avg"],
                        "tot": stat["total"],
                    }
                )
    else:
        for stat in stats:
            recieving = False
            cursor = db.execute(
                "SELECT * from players where id = ?", [stat["playerid"]]
            )
            player = cursor.fetchone()
            cursor.close()
            cursor = db.execute(
                "select * from passing where playerid = ? and year = ?",
                [player["id"], year],
            )
            result = cursor.fetchone()
            cursor.close()
            if result != None:
                oldTeam = result["teamid"]
            cursor = db.execute(
                "select * from rushing where playerid = ? and year = ?",
                [player["id"], year],
            )
            result = cursor.fetchone()
            cursor.close()
            if result != None:
                oldTeam = result["teamid"]
            cursor = db.execute(
                "select * from recieving where playerid = ? and year = ?",
                [player["id"], year],
            )
            result = cursor.fetchone()
            cursor.close()
            if result != None:
                oldTeam = result["team"]
                recieving = True

            players.append(
                {
                    "rank": stat["rank"],
                    "name": player["name"],
                    "pos": player["pos"],
                    "team": player["teamid"],
                    "oldteam": oldTeam,
                    "weeks": stat["weeks"],
                    "avg": stat["avg"],
                    "tot": stat["total"],
                }
            )
    for player in players:
        cursor = db.execute("select * from teams where id = ?", [player["team"]])
        result = cursor.fetchone()
        cursor.close()
        player["team"] = result["abbrv"]
        cursor = db.execute("select * from teams where id = ?", [player["oldteam"]])
        result = cursor.fetchone()
        cursor.close()
        player["oldteam"] = result["abbrv"]
        player["keys"] = player.keys()
        weeks = player["weeks"].split(" ")
        player["weeks"] = []
        for week in weeks:
            if week not in ["", " "]:
                player["weeks"].append(week)
    return players


def loadRosters():
    db = get_db("databasecopy.db")
    playerdata = []
    driver = webdriver.Firefox()
    driver.maximize_window()
    for team in createTeamDict():
        if team["id"] != 33:
            if team["abbrv"] == "WAS":
                url = "https://www.espn.com/nfl/team/roster/_/name/wsh/washington-commanders"
            else:
                url = (
                    "https://www.espn.com/nfl/team/roster/_/name/"
                    + team["abbrv"].lower()
                    + "/"
                    + team["name"].replace(" ", "-").lower()
                )
            driver.get(url)
            player = {}
            time.sleep(3)
            players = driver.find_elements(
                By.CLASS_NAME, "Table__TR.Table__TR--lg.Table__even"
            )
            for member in players:
                player = {}
                player["teamid"] = team["id"]
                elements = member.find_elements(By.TAG_NAME, "td")
                player["name"] = (
                    elements[1].find_element(By.CLASS_NAME, "AnchorLink").text
                )
                img = member.find_element(By.CSS_SELECTOR, "img")
                player["photo"] = (
                    img.get_attribute("src").split("&")[0] + "&w=350&h=254"
                )
                try:
                    player["num"] = int(
                        elements[1].find_element(By.TAG_NAME, "span").text
                    )
                except NoSuchElementException:
                    player["num"] = None

                player["pos"] = elements[2].find_element(By.TAG_NAME, "div").text
                player["age"] = elements[3].find_element(By.TAG_NAME, "div").text
                player["exp"] = elements[6].find_element(By.TAG_NAME, "div").text
                if player["pos"] in ["QB", "RB", "WR", "TE", "PK"]:
                    playerdata.append(player)
    driver.close()
    db.execute(
        "update players set teamid = ? where teamid != ? and pos != ?", [33, 33, "dst"]
    )
    for player in playerdata:
        names = player["name"].split(" ")
        full = "%" + names[0] + " " + names[1] + "%"
        last = "%" + names[1] + "%"
        initial = names[0][:1] + "%"
        cursor = db.execute(
            "select * from players where name like ? and pos = ?",
            [full, player["pos"]],
        )
        results = cursor.fetchall()
        cursor.close()
        if len(results) == 0 or player["exp"] == "R":
            addPlayercopy(player)
            print(player["name"])
        else:
            db.execute(
                "update players set teamid = ? where name = ?",
                [player["teamid"], player["name"]],
            )
        db.commit()
    today = date.today()
    db.execute(
        "update edit set month = ?, day = ?, year = ? where data = ?",
        [today.month, today.day, today.year, "rosters"],
    )
    db.close()
    return
