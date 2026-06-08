import datetime
import sqlite3
import time

import requests
from bs4 import BeautifulSoup
from flask import g, jsonify, request, url_for
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from .database import autoData

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
teamsDict = []


def createTeamDict():
    teamDict = []
    db = get_db()
    cursor = db.execute("select id, name, abbrv, conf, div, logo from teams")
    results = cursor.fetchall()
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
    return teamDict


def connect_db():
    sql = sqlite3.connect("./database.db")
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    if not hasattr(g, "sqlite3"):
        g.sqlite3_db = connect_db()
    return g.sqlite3_db


def create_user(email, firstName, lastName, password):
    db = get_db()
    db.execute(
        "INSERT INTO users (email, firstName, lastName, password) VALUES (?, ?, ?, ?)",
        [email, firstName, lastName, password],
    )
    db.commit()
    return


def dataEmpty(table):
    db = get_db()
    cursor = db.execute("select * from " + table)
    results = cursor.fetchall()
    if len(results) == 0:
        return True
    else:
        return False


def get_user(user_id):
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE id = ?", [user_id])
    result = cursor.fetchone()
    if not result:
        return jsonify({"error": "User not found"})
    return f"<h1>The Id is {result['id']}.<br> The Name is {result['name']}. <br> The age is {result['age']}. </h1>"


def update_user(user_id):
    db = get_db()
    name = request.json["name"]
    age = request.json["age"]
    db.execute("UPDATE users SET name = ?, age = ? WHERE id = ?", [name, age, user_id])
    db.commit()
    return jsonify({"message": "User updated successfully!"})


def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", [user_id])
    db.commit()
    return jsonify({"message": "User deleted successfully!"})


def loadTeamInfo():

    if dataEmpty(table="teams"):
        db = get_db()
        for i in range(0, len(teams)):
            db.execute(
                "INSERT INTO teams (name,abbrv,conf,div,logo) VALUES (?,?,?,?,?)",
                [teams[i], abbrv[i], conf[i], div[i], "logos/" + abbrv[i] + ".webp"],
            )
        db.commit()
        print("Team data loaded.")
    else:
        print("Team data already exists.")

    return


def loadPlayers():
    db = get_db()
    if dataEmpty("players"):
        teamDict = createTeamDict()
        playerdata = []
        for team in teamDict:
            if team["abbrv"] == "WAS":
                url = "https://www.espn.com/nfl/team/roster/_/name/wsh/washington-commanders"
            else:
                url = (
                    "https://www.espn.com/nfl/team/roster/_/name/"
                    + team["abbrv"].lower()
                    + "/"
                    + team["name"].replace(" ", "-").lower()
                )
            driver = webdriver.Firefox()
            driver.maximize_window()
            driver.get(url)
            player = {}
            players = driver.find_elements(
                By.CLASS_NAME, "Table__TR.Table__TR--lg.Table__even"
            )
            for member in players:
                player = {}
                cursor = db.execute(
                    "select * from teams where abbrv = ?", [team["abbrv"]]
                )
                result = cursor.fetchone()
                player["teamid"] = result["id"]
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
                playerdata.append(player)
            driver.close()

        db = get_db()
        for person in playerdata:
            if person["pos"] in ["QB", "RB", "WR", "TE", "PK"]:
                if person["num"] != None:
                    db.execute(
                        "INSERT INTO players (teamid, name, num, pos, age, exp, photo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        [
                            person["teamid"],
                            person["name"],
                            person["num"],
                            person["pos"],
                            person["age"],
                            person["exp"],
                            person["photo"],
                        ],
                    )
                else:
                    db.execute(
                        "INSERT INTO players (teamid, name, pos, age, exp, photo) VALUES (?, ?, ?, ?, ?, ?)",
                        [
                            person["teamid"],
                            person["name"],
                            person["pos"],
                            person["age"],
                            person["exp"],
                            person["photo"],
                        ],
                    )
                db.commit()
        print("Player data loaded.")
        return

    else:
        print("Player data exists.")

    return


def loadPlayerPhoto(name):

    url = (
        "https://www.fantasypros.com/nfl/players/"
        + name.lower().replace(" ", "-")
        + ".php"
    )
    result = requests.get(url)
    doc = BeautifulSoup(result.text, "html.parser")
    href = doc.find_all("source")

    if len(href) > 1:
        if "https" not in href[1].attrs["srcset"].split(" ")[2]:
            return
        else:
            return href[1].attrs["srcset"].split(" ")[2]

    return


def addPlayer(player):
    db = get_db()
    cursor = db.execute("SELECT * FROM players WHERE name = ?", [player["name"]])
    result = cursor.fetchone()
    if result == None:
        db.execute(
            "INSERT INTO players (teamid, name, num, pos, age, exp, photo) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                33,
                player["name"],
                0,
                player["pos"],
                player["age"],
                player["exp"],
                loadPlayerPhoto(player["name"]),
            ],
        )
        db.commit()


def getPlayerStats(team, year):
    db = get_db()
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


def getPlayers():
    db = get_db()
    cursor = db.execute("SELECT * from players")
    result = cursor.fetchall()
    return result


def getFantasyStats(year):
    db = get_db()
    cursor = db.execute("SELECT * from fantasy where year = ?", [year])
    result = cursor.fetchall()
    return result


def getTeams():
    db = get_db()
    cursor = db.execute("SELECT * from teams")
    results = cursor.fetchall()
    return results


def getFantasyPageStats(year, position):
    fantasy = getFantasyStats(year)
    db = get_db()
    cursor = db.execute("SELECT * from fantasy where year = ?", [year])
    stats = cursor.fetchall()
    players = []

    if position != "Select Position":
        for stat in stats:
            recieving = False
            cursor = db.execute(
                "SELECT * from players where id = ?", [stat["playerid"]]
            )
            player = cursor.fetchone()
            if player["pos"] == position:
                cursor = db.execute(
                    "select * from passing where playerid = ? and year = ?",
                    [player["id"], year],
                )
                result = cursor.fetchone()
                if result != None:
                    oldTeam = result["teamid"]
                cursor = db.execute(
                    "select * from rushing where playerid = ? and year = ?",
                    [player["id"], year],
                )
                result = cursor.fetchone()
                if result != None:
                    oldTeam = result["teamid"]
                cursor = db.execute(
                    "select * from recieving where playerid = ? and year = ?",
                    [player["id"], year],
                )
                result = cursor.fetchone()
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
            cursor = db.execute(
                "select * from passing where playerid = ? and year = ?",
                [player["id"], year],
            )
            result = cursor.fetchone()
            if result != None:
                oldTeam = result["teamid"]
            cursor = db.execute(
                "select * from rushing where playerid = ? and year = ?",
                [player["id"], year],
            )
            result = cursor.fetchone()
            if result != None:
                oldTeam = result["teamid"]
            cursor = db.execute(
                "select * from recieving where playerid = ? and year = ?",
                [player["id"], year],
            )
            result = cursor.fetchone()
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
        player["team"] = result["abbrv"]
        cursor = db.execute("select * from teams where id = ?", [player["oldteam"]])
        result = cursor.fetchone()
        player["oldteam"] = result["abbrv"]
        player["keys"] = player.keys()
        weeks = player["weeks"].split(" ")
        player["weeks"] = []
        for week in weeks:
            if week not in ["", " "]:
                player["weeks"].append(week)
    return players


def loadProjections():
    db = get_db()
    cursor = db.execute("Select * from espnproj")
    espnproj = cursor.fetchall()
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
            cursor = db.execute(
                "select * from players where name = ?", [listPlayers[x]["name"]]
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
                print(listPlayers["name"])
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
    else:
        print("FP Projections Exist.")
    cursor = db.execute("Select * from CBSranks")
    result = cursor.fetchall()
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
            ).text.split(" ")[1]
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
            cursor = db.execute("select * from teams where abbrv = ?", [player["team"]])
            result = cursor.fetchone()
            if result != None:
                cursor = db.execute(
                    "select * from players where teamid = ? and pos = ?",
                    [result["id"], player["pos"]],
                )
                result = cursor.fetchall()
                x = 0
                while x < len(result):
                    if (
                        result[x]["name"].split(" ")[1] == player["name"].split(" ")[1]
                        and result[x]["name"][0] == player["name"][0]
                    ):
                        player["found"] = True
                        player["id"] = result[x]["id"]
                        x = 1000
                    else:
                        player["found"] = False
                    x = x + 1
            else:
                player["found"] = False
            if player["found"] == False:
                print(player["name"])
                cursor = db.execute("select * from players where teamid = ?", [33])
                fa = cursor.fetchall()
                for person in fa:
                    if (
                        person["name"].split(" ")[1] == player["name"].split(" ")[1]
                        and person["pos"] == player["pos"]
                    ):
                        player["id"] = person["id"]
                        player["found"] = True
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

    return


def grabRanks():
    db = get_db()
    cursor = db.execute("select * from espnproj")
    espnproj = cursor.fetchall()
    cursor = db.execute("select * from FPranks")
    FPranks = cursor.fetchall()
    cursor = db.execute("select * from CBSranks")
    CBSranks = cursor.fetchall()
    cursor = db.execute("select * from avgranks")
    avgranks = cursor.fetchall()
    return [espnproj, FPranks, CBSranks, avgranks]


def loadAvgRanks():
    db = get_db()
    cursor = db.execute("select * from avgranks")
    result = cursor.fetchall()
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
    return


def getPlayer(id):
    db = get_db()
    cursor = db.execute("select * from players where id = ?", [id])
    player = cursor.fetchone()
    return player


def getTeam(id):
    db = get_db()
    cursor = db.execute("select * from teams where id = ?", [id])
    team = cursor.fetchone()
    return team


def grabPlayerData(players):
    db = get_db()
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
    return playerdata


def getTeams():
    db = get_db()
    cursor = db.execute("SELECT * from teams")
    teams = cursor.fetchall()
    return teams


def getPlayers():
    db = get_db()
    cursor = db.execute("SELECT * from players")
    players = cursor.fetchall()
    return players


def addSeason(stats, player, year, team):
    db = get_db()
    cursor = db.execute("SELECT * FROM players WHERE name = ?", [player["name"]])
    result = cursor.fetchone()
    cursor = db.execute("SELECT * FROM teams WHERE abbrv = ?", [team])
    team = cursor.fetchone()
    add = True
    if stats[0] == "Passing":
        cursor = db.execute("SELECT * FROM passing WHERE playerid = ?", [result["id"]])
        seasons = cursor.fetchall()
        if len(seasons) != 0:
            for season in seasons:
                if season["year"] == year and season["teamid"] == team["id"]:
                    add = False
        if add == True:
            data = [result["id"]] + [team["id"]] + [year] + stats[1 : len(stats)]
            x = 3
            db.execute(
                "INSERT INTO passing (playerid, teamid, year,  gp, cmp, att, percent, yds, avg, pergame, lng, td, interceptions, sack, ysl, rtg) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                data,
            )
    elif stats[0] == "Rushing":
        cursor = db.execute("SELECT * FROM rushing WHERE playerid = ?", [result["id"]])
        seasons = cursor.fetchall()
        if len(seasons) != 0:
            for season in seasons:
                if season["year"] == year and season["teamid"] == team["id"]:
                    add = False
        if add == True:
            data = [result["id"]] + [team["id"]] + [year] + stats[1 : len(stats)]
            db.execute(
                "INSERT INTO rushing (playerid, teamid, year,  gp, car, yds, avg, lng, big, td, pergame, fum, lst, fd) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                data,
            )
    else:
        cursor = db.execute(
            "SELECT * FROM recieving WHERE playerid = ?", [result["id"]]
        )
        seasons = cursor.fetchall()
        if len(seasons) != 0:
            for season in seasons:
                if season["year"] == year and season["team"] == team["id"]:
                    add = False
        if add == True:
            data = [result["id"]] + [team["id"]] + [year] + stats[1 : len(stats)]
            db.execute(
                "INSERT INTO recieving (playerid, team, year, gp, rec, tgts, yds, avg, td, lng, big, pergame, fum, lst, yac, fd) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                data,
            )
    db.commit()


def loadStats():
    db = get_db()
    cursor = db.execute("SELECT * FROM passing")
    result = cursor.fetchall()
    if len(result) == 0:
        teamDict = createTeamDict()
        seasons = []
        for team in teamDict:
            if team["id"] != 33:
                if team["abbrv"] == "WAS":
                    url1 = "https://www.espn.com/nfl/team/stats/_/name/wsh/season/2022/seasontype/2"
                    url2 = "https://www.espn.com/nfl/team/stats/_/name/wsh/season/2021/seasontype/2"
                    url3 = "https://www.espn.com/nfl/team/stats/_/name/wsh/season/2020/seasontype/2"
                else:
                    url1 = (
                        "https://www.espn.com/nfl/team/stats/_/name/"
                        + team["abbrv"].lower()
                        + "/season/2022/seasontype/2"
                    )
                    url2 = (
                        "https://www.espn.com/nfl/team/stats/_/name/"
                        + team["abbrv"].lower()
                        + "/season/2021/seasontype/2"
                    )
                    url3 = (
                        "https://www.espn.com/nfl/team/stats/_/name/"
                        + team["abbrv"].lower()
                        + "/season/2020/seasontype/2"
                    )
                urls = [url1, url2, url3]
                for url in urls:
                    if url == url1:
                        year = 2022
                    elif url == url2:
                        year = 2021
                    else:
                        year = 2020
                    season = {"team": team["id"], "year": year}
                    driver = webdriver.Firefox()
                    driver.maximize_window()
                    driver.get(url)
                    tables = driver.find_elements(
                        By.CLASS_NAME,
                        "ResponsiveTable.ResponsiveTable--fixed-left.mt5.remove_capitalize",
                    )
                    for table in tables:
                        cat = table.find_element(By.CLASS_NAME, "Table__Title").text
                        if cat in ["Passing", "Rushing", "Receiving"]:
                            season[cat] = []
                            namescontainer = table.find_element(
                                By.CLASS_NAME,
                                "Table.Table--align-right.Table--fixed.Table--fixed-left",
                            )
                            names = namescontainer.find_elements(
                                By.CLASS_NAME, "AnchorLink"
                            )
                            positions = namescontainer.find_elements(
                                By.CLASS_NAME, "font10"
                            )
                            statstable = table.find_element(
                                By.CLASS_NAME, "Table__Scroller"
                            )
                            statrows = statstable.find_elements(
                                By.CLASS_NAME, "Table__TR.Table__TR--sm.Table__even"
                            )
                            x = 0
                            while x < len(names):
                                stats = statrows[x].find_elements(
                                    By.CLASS_NAME, "Table__TD"
                                )
                                player = {}
                                player["name"] = names[x].text
                                position = positions[x].text
                                cursor = db.execute(
                                    "Select * from players where name = ?",
                                    [player["name"]],
                                )
                                result = cursor.fetchone()
                                if result == None:
                                    urlp = names[x].get_attribute("href")
                                    driver1 = webdriver.Firefox()
                                    driver.maximize_window()
                                    driver1.get(urlp)
                                    playerinfo = driver1.find_element(
                                        By.CLASS_NAME, "PlayerHeader__Left"
                                    )
                                    photo = playerinfo.find_elements(
                                        By.TAG_NAME, "img"
                                    )[1].get_attribute("src")
                                    about = playerinfo.find_element(
                                        By.CLASS_NAME,
                                        "PlayerHeader__Bio_List.flex.flex-column.list.clr-gray-04",
                                    )
                                    aboutinfo = about.find_elements(By.TAG_NAME, "li")
                                    for li in aboutinfo:
                                        if (
                                            li.find_element(By.CLASS_NAME, "ttu").text
                                            == "BIRTHDATE"
                                        ):
                                            age = 2023 - int(
                                                li.find_element(
                                                    By.CLASS_NAME, "fw-medium.clr-black"
                                                )
                                                .text.split("/")[2]
                                                .split("(")[0]
                                                .split(" ")[0]
                                            )
                                            print(age)
                                    db.execute(
                                        "insert into players (teamid,name,pos,age,photo) values (?,?,?,?,?)",
                                        [33, player["name"], position, age, photo],
                                    )
                                    db.commit()
                                    driver1.close()
                                    cursor = db.execute(
                                        "Select * from players where name = ?",
                                        [player["name"]],
                                    )
                                    result = cursor.fetchone()
                                player["gp"] = int(stats[0].text)
                                if cat == "Passing":
                                    player["cmp"] = int(stats[1].text)
                                    player["att"] = int(stats[2].text)
                                    player["percent"] = float(stats[3].text)
                                    player["yds"] = int(stats[4].text.replace(",", ""))
                                    player["avg"] = float(stats[5].text)
                                    player["pergame"] = float(stats[6].text)
                                    player["lng"] = int(stats[7].text)
                                    player["td"] = int(stats[8].text)
                                    player["int"] = int(stats[9].text)
                                    player["id"] = result["id"]
                                    season[cat].append(player)
                                elif cat == "Rushing":
                                    player["car"] = int(stats[1].text)
                                    player["yds"] = int(stats[2].text.replace(",", ""))
                                    player["avg"] = float(stats[3].text)
                                    player["lng"] = int(stats[4].text)
                                    player["big"] = int(stats[5].text)
                                    player["td"] = int(stats[6].text)
                                    player["pergame"] = float(stats[7].text)
                                    player["fum"] = int(stats[8].text)
                                    player["id"] = result["id"]
                                    season[cat].append(player)
                                elif cat == "Receiving":
                                    player["rec"] = int(stats[1].text)
                                    player["tgts"] = int(stats[2].text)
                                    player["yds"] = int(stats[3].text.replace(",", ""))
                                    player["avg"] = float(stats[4].text)
                                    player["td"] = int(stats[5].text)
                                    player["lng"] = int(stats[6].text)
                                    player["big"] = int(stats[7].text)
                                    player["pergame"] = float(stats[8].text)
                                    player["fum"] = int(stats[9].text)
                                    player["yac"] = int(stats[11].text)
                                    player["id"] = result["id"]
                                    season[cat].append(player)
                                x = x + 1
                    driver.close()
                    seasons.append(season)
        print(seasons[0]["Passing"])
        print(seasons[1]["Passing"])
        for season in seasons:
            for passer in season["Passing"]:
                values = [
                    passer["id"],
                    season["team"],
                    season["year"],
                    passer["gp"],
                    passer["cmp"],
                    passer["att"],
                    passer["percent"],
                    passer["yds"],
                    passer["avg"],
                    passer["pergame"],
                    passer["lng"],
                    passer["td"],
                    passer["int"],
                ]
                db.execute(
                    "insert into passing (playerid,teamid,year,gp,cmp,att,percent,yds,avg,pergame,lng,td,interceptions) values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    values,
                )
            for rusher in season["Rushing"]:
                values = [
                    rusher["id"],
                    season["team"],
                    season["year"],
                    rusher["gp"],
                    rusher["car"],
                    rusher["yds"],
                    rusher["avg"],
                    rusher["lng"],
                    rusher["big"],
                    rusher["td"],
                    rusher["pergame"],
                    rusher["fum"],
                ]
                db.execute(
                    "insert into rushing (playerid, teamid, year,  gp, car, yds, avg, lng, big, td, pergame, fum) values (?,?,?,?,?,?,?,?,?,?,?,?)",
                    values,
                )
            for reciever in season["Receiving"]:
                values = [
                    reciever["id"],
                    season["team"],
                    season["year"],
                    reciever["gp"],
                    reciever["rec"],
                    reciever["tgts"],
                    reciever["yds"],
                    reciever["avg"],
                    reciever["td"],
                    reciever["lng"],
                    reciever["big"],
                    reciever["pergame"],
                    reciever["fum"],
                    reciever["yac"],
                ]
                db.execute(
                    "insert into recieving (playerid, team, year, gp, rec, tgts, yds, avg, td, lng, big, pergame, fum, yac) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    values,
                )
        db.commit()
        print("Stats Loaded!")
    else:
        print("Existing Stats.")
    return


def loadFantasyStats():
    db = get_db()
    cursor = db.execute("SELECT * FROM fantasy")
    result = cursor.fetchall()
    if len(result) == 0:
        url1 = "https://www.fantasypros.com/nfl/reports/leaders/ppr.php?year=2022"
        url2 = "https://www.fantasypros.com/nfl/reports/leaders/ppr.php?year=2021"
        url3 = "https://www.fantasypros.com/nfl/reports/leaders/ppr.php?year=2020"
        urls = [
            {"url": url1, "year": 2022},
            {"url": url2, "year": 2021},
            {"url": url3, "year": 2020},
        ]
        players = []
        for url in urls:
            driver = webdriver.Firefox()
            driver.maximize_window()
            driver.get(url["url"])
            table = driver.find_element(By.TAG_NAME, "tbody")
            row = table.find_elements(By.TAG_NAME, "tr")
            x = 0
            while x < 300:
                player = {}
                player["year"] = url["year"]
                player["rank"] = int(
                    row[x].find_element(By.CLASS_NAME, "player-rank").text
                )
                player["name"] = row[x].find_element(By.CLASS_NAME, "player-name").text
                info = row[x].find_elements(By.CLASS_NAME, "center")
                player["pos"] = info[0].text
                player["team"] = info[1].find_element(By.TAG_NAME, "a").text
                player["tot"] = float(info[-1].text)
                player["avg"] = float(info[-2].text)
                weeks = ""
                y = 2
                while y < (len(info) - 2):
                    if y == 2:
                        weeks = info[y].text
                    else:
                        weeks = weeks + " " + (info[y].text)
                    y = y + 1
                player["weeks"] = weeks
                players.append(player)
                x = x + 1
            driver.close()
        prevrank = 1
        x = 0
        while x < len(players):
            if x > 0:
                if players[x]["year"] != players[x - 1]["year"]:
                    prevrank = 1
            if players[x]["pos"] not in ["K", "DST"]:
                posrank = 1
                if x <= 299:
                    y = 0
                elif x > 299 and x <= 599:
                    y = 300
                else:
                    y = 600
                while y < x:
                    if players[y]["pos"] == players[x]["pos"]:
                        posrank = posrank + 1
                    y = y + 1
                players[x]["posrank"] = players[x]["pos"] + str(posrank)
                cursor = db.execute(
                    "SELECT * FROM players where name = ?", [players[x]["name"]]
                )
                result = cursor.fetchone()
                if result == None:
                    name = (
                        players[x]["name"].split(" ")[0]
                        + " "
                        + players[x]["name"].split(" ")[1]
                    )
                    cursor = db.execute("SELECT * FROM players where name = ?", [name])
                    result = cursor.fetchone()
                    if result != None:
                        players[x]["id"] = result["id"]
                        players[x]["name"] = (
                            players[x]["name"].split(" ")[0]
                            + " "
                            + players[x]["name"].split(" ")[1]
                        )
                else:
                    players[x]["id"] = result["id"]
                if players[x]["team"] == "JAC":
                    players[x]["team"] = "JAX"
                cursor = db.execute(
                    "select * from rushing where playerid = ? and year = ?",
                    [players[x]["id"], players[x]["year"]],
                )
                result = cursor.fetchone()
                if result != None:
                    players[x]["team"] = result["teamid"]
                else:
                    cursor = db.execute(
                        "select * from recieving where playerid = ? and year = ?",
                        [players[x]["id"], players[x]["year"]],
                    )
                    result = cursor.fetchone()
                    if result != None:
                        players[x]["team"] = result["team"]
                    else:
                        cursor = db.execute(
                            "select * from passing where playerid = ? and year = ?",
                            [players[x]["id"], players[x]["year"]],
                        )
                        result = cursor.fetchone()
                        players[x]["team"] = result["teamid"]
                players[x]["rank"] = prevrank
                prevrank = prevrank + 1
                values = [
                    players[x]["id"],
                    players[x]["team"],
                    players[x]["year"],
                    players[x]["rank"],
                    players[x]["avg"],
                    players[x]["tot"],
                    players[x]["weeks"],
                    players[x]["posrank"],
                ]
                db.execute(
                    "insert into fantasy (playerid, teamid, year, rank, avg, total, weeks, posrank) values (?,?,?,?,?,?,?,?)",
                    values,
                )
            x = x + 1
        db.commit()
        print("Fantasy Stats Loaded!")
    else:
        print("Fantasy Stats Exist.")

    return


def loadDST():
    db = get_db()
    teams = createTeamDict()
    cursor = db.execute('select * from players where pos = "DST"')
    result = cursor.fetchall()
    if len(result) < 1:
        for team in teams:
            if team["name"] != "FA":
                db.execute(
                    "INSERT INTO players (teamid, name, pos, photo) VALUES (?, ?, ?, ?)",
                    [
                        team["id"],
                        team["name"],
                        "DST",
                        url_for("static", filename=team["logo"]),
                    ],
                )
        db.commit()
        print("DSTs Added!")
    else:
        print("DST Data Exists.")
    return



def loadDB():
    loadTeamInfo()
    loadPlayers()
    loadStats()
    loadFantasyStats()
    loadProjections()
    loadDST()
    autoData()
    return
