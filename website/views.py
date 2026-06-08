from flask import Blueprint, flash, redirect, render_template, request, url_for

from .database import (
    autoData,
    get_db,
    getFantasyPageStats,
    getFantasyStats,
    getPlayer,
    getPlayers,
    getPlayerStats,
    getTeam,
    grabPlayerData,
    grabRanks,
    loadProjections,
)
from .functions import createTeamDict, dataEmpty, getTeams, loadDB

views = Blueprint('views', __name__)

@views.route('/home')
def home():
    
    autoData()
    return render_template("home.html")

@views.route('/team_stats', methods=['GET', 'POST'])
def team_stats():
    
    teams = createTeamDict()
    years = ['Current Roster','2022','2021','2020']
    
    if request.method == 'POST':

        team = request.form.get('team')
        year = request.form.get('year')
    
        if team == 'Select Team':
            flash("Select a team.",category='error')
        elif year == 'Select Year':
            flash("Select a year.",category='error')
        else:
            if year == 'Current Roster':
              print('okay')
            else:
              data = getPlayerStats(team,year,'databasecopy.db')
              passers = data[0]
              rushers = data[1]
              recievers = data[2]
        return render_template("team_stats.html", nfl_teams=teams,team=team,options_year=years,year=year,passers=passers,rushers=rushers,recievers= recievers)

    return render_template("team_stats.html",nfl_teams=teams,team='Select Team',options_year=years,year='Select Year',passers=[],rushers=[],recievers=[])

@views.route('/fantasy', methods=['GET', 'POST'])
def fantasy():
    
    years = ['2023 Projections','2022','2021','2020']
    positions = ['QB','RB','WR','TE','DEF','K']
    
    if request.method == 'POST':

        year = request.form.get('year')
        position = request.form.get('position')
    
        if year == 'Select Year':
            flash("Select a year.",category='error')
        else:
            fantasy = getFantasyPageStats(int(year),position)
            
        return render_template("fantasy.html",options_year=years,year=year,positions=positions,position=position,fantasy=fantasy)

    return render_template("fantasy.html",options_year=years,year='Select Year',positions=positions,position='Select Position',fantasy=[])

@views.route('/player')
def player():
    players = request.args.getlist('players')
    playerdata = grabPlayerData(players)
    years = [2022,2021,2020]
    teams = getTeams()
    return render_template("player.html",playerdata=playerdata,years=years,teams=teams)

@views.route('/compare_players', methods=['GET', 'POST'])
def compare_players():
    players = getPlayers()
    teams = getTeams()
    playernames=[]
    if request.method == 'POST':
        num = request.form.get('num')
        if num!=None:
            num = int(num)
            playerdata = []
        else:
            playerids = []
            x=1
            while x <= 5:
                try:
                    playernames.append(request.form.get('player'+str(x)))
                    x = x + 1
                except ValueError as e:
                    x = 6
            for player in players:
                for name in playernames:
                    if player['name']==name:
                        playerids.append(player['id'])
            playerdata = grabPlayerData(playerids)

        return render_template("compare_players.html",players=players,playerdata=playerdata,teams=teams,num=num)

    return render_template("compare_players.html",players=players,playerdata=None,teams=teams,num=None)

@views.route('/ranks',methods=['GET', 'POST'])
def ranks():
    ranks = grabRanks()
    players = getPlayers()
    selector = [{'ESPN Ranks':0,'FP Ranks':1,'CBS Ranks':2,'Average Rankings':3}]
    db = get_db('databasecopy.db')
    if request.method == 'POST':
        update = request.form.get('update')
        if update!=None:
            db.execute('drop table espnproj')
            db.execute('drop table FPranks')
            db.execute('drop table CBSranks')
            db.execute('drop table avgranks')
            db.execute('create table espnproj (rank int, playerid references players(id), car text, rushyds text, rushtd text, tar text, rec text, recyds text, rectds text, compperatt text, yds text, passtd text, interceptions text, fpts text, posrank text)')
            db.execute('create table FPranks (rank int, playerid references players(id), posrank text, SOS text)')
            db.execute('create table CBSranks (rank int, playerid references players(id), posrank text)')
            db.execute('create table avgranks (rank integer, playerid references players(id), posrank text, SOS text)')
            loadProjections()
        try:
            index = int(request.form.get('index'))
        except TypeError as e:
            x=0
            players=getPlayers()
            for player in players:
                fav = request.form.get(player['name'])
                if fav == None and player['fav']=='True':
                    db.execute('update players set fav = ? where id = ?',['False',player['id']])
                if fav != None:
                    db.execute('update players set fav = ? where id = ?',['True',player['id']])
            db.commit()
            return render_template("ranks.html",selector=selector,data=[])
        info = ranks[index]
        data = []
        for proj in info:
            player = {}
            playerinfo = getPlayer(proj['playerid'])
            teaminfo = getTeam(playerinfo['teamid'])
            player['name']=playerinfo['name']
            player['id']=playerinfo['id']
            player['team']=teaminfo['abbrv']
            player['fav']=playerinfo['fav']
            player['keys']=[]
            for key in proj.keys():
                if key not in ['playerid','rank','posrank']:
                    player['keys'].append(key)
            player['data']=proj
            data.append(player)
        return render_template("ranks.html",selector=selector,data=data)
    return render_template("ranks.html",selector=selector,data=[])

@views.route('/draft_analyzer',methods=['GET', 'POST'])
def draft_analyzer():
    db = get_db('databasecopy.db')
    options = [4,8,10,12,16]
    players=getPlayers()
    if request.method == 'POST':
        size = request.form.get('size')
        if size != None:
            size = int(size)
            labels = []
            for i in range(1,size+1):
                labels.append('Team '+str(i))
            return render_template("draft_analyzer.html",options=[],labels=labels,size=size,players=players)
        else:
            db.execute('drop table availablePlayers')
            db.execute('drop table draftTeams')
            db.execute('drop table picks')
            db.execute('create table availablePlayers (rank integer, playerid integer references players(id),teamid references teams(id), name text, num integer, pos text, age integer, exp text, photo text,fav text)')
            db.execute('create table draftTeams (id integer primary key autoincrement,name text,keeper integer,round integer,myteam text)')
            db.execute('create table picks (no integer primary key autoincrement, teamid references draftTeams(id), playerid integer)')
            db.commit()

            teaminfo = []
            for i in range(1,17):
                key = 'Team '+str(i)
                teamname = request.form.get(key)
                if teamname == '':
                    flash("Enter a team name for "+key+'.',category='error')
                    return render_template("draft_analyzer.html",options=options,labels=[],size=None,players=players)
                teamkeeper = request.form.get(key+'keeper')
                keeperrd = request.form.get(key+'round')
                check = request.form.get(key+'myteam')
                if check!=None:
                    myteam = 'True'
                    teamname= 'Your Team'
                else:
                    myteam = 'False'
                if (teamkeeper =='' and keeperrd!=''):
                    flash("Enter keeper name for "+key+'.',category='error')
                    return render_template("draft_analyzer.html",options=options,labels=[],size=None,players=players)
                if (teamkeeper !='' and keeperrd==''):
                    flash("Enter keeper round for "+key+'.',category='error')
                    return render_template("draft_analyzer.html",options=options,labels=[],size=None,players=players)
                if keeperrd!=None:
                    try:
                        keeperrd = int(keeperrd)
                    except ValueError as e:
                        keeperrd = None
                team = {'name':teamname,'round':keeperrd,'myteam':myteam}
                if keeperrd!=None:
                    for player in players:
                        if player['name']==teamkeeper:
                            team['keeper']=player['id']
                else:
                    team['keeper']=None
                if teamname != None:
                    teaminfo.append(team)
            order=[]
            for team in teaminfo:
                db.execute('insert into draftTeams (name,keeper,round,myteam) values (?,?,?,?)',[team['name'],team['keeper'],team['round'],team['myteam']])
            db.commit()
            ranks = grabRanks()
            for rank in ranks[3]:
                for player in players:
                    if player['id']==rank['playerid']:
                        values = [rank['rank'],player['id'],player['teamid'],player['name'],player['num'],player['pos'],player['age'],player['exp'],player['photo'],player['fav']]
                        db.execute('insert into availablePlayers (rank, playerid, teamid, name, num, pos, age, exp, photo, fav) values (?,?,?,?,?,?,?,?,?,?)',values)
            db.commit()
            cursor = db.execute('select * from players where pos in ("DST","PK")')
            dstk = cursor.fetchall()
            for item in dstk:
                values = [1000,item['id'],item['teamid'],item['name'],item['pos'],item['photo'],'False']
                db.execute('insert into availablePlayers (rank, playerid, teamid, name, pos, photo,fav) values (?,?,?,?,?,?,?)',values)
            cursor = db.execute('select * from draftTeams')
            teaminfo = cursor.fetchall()
            for x in range(1,17):
                if x % 2 !=0:
                    for team in teaminfo:
                        if x!=team['round']:
                            db.execute('insert into picks (teamid) values (?)',[team['id']])
                        else:
                            db.execute('insert into picks (teamid,playerid) values (?,?)',[team['id'],team['keeper']])
                            db.execute('delete from availablePlayers where playerid = ?',[team['keeper']])
                else:
                    i=-1
                    while i>(-1*(len(teaminfo)+1)):
                        if x!=teaminfo[i]['round']:
                            db.execute('insert into picks (teamid) values (?)',[teaminfo[i]['id']])
                        else:
                            db.execute('insert into picks (teamid,playerid) values (?,?)',[teaminfo[i]['id'],teaminfo[i]['keeper']])
                            db.execute('delete from availablePlayers where playerid = ?',[teaminfo[i]['keeper']])
                        i=i-1
                    db.commit()
            cursor = db.execute('select * from picks')
            result = cursor.fetchall()
                
            return render_template("active_draft.html",availablePlayers=None,players=players)
            
    return render_template("draft_analyzer.html",options=options,labels=[],size=None,players=players)

@views.route('/active_draft', methods=['GET', 'POST'])
def active_draft():
    db = get_db('databasecopy.db')
    cursor = db.execute('select * from draftTeams')
    teams = cursor.fetchall()
    cursor = db.execute('select * from avgranks')
    avgranks = cursor.fetchall()
    cursor = db.execute('select * from espnproj')
    espn = cursor.fetchall()
    cursor = db.execute('select * from FPranks')
    fp = cursor.fetchall()
    cursor = db.execute('select * from CBSranks')
    cbs = cursor.fetchall()
    cursor = db.execute('select * from teams')
    nfl = cursor.fetchall()
    myTeam = {'QB':'','RB1':'','RB2':'','WR1':'','WR2':'','TE':'','FLEX':'','DST':'','PK':'','BENCH':[]}
    cursor = db.execute("select * from draftTeams where myteam = 'True'")
    myteamid = cursor.fetchone()
    if myteamid['keeper']!=None:
        cursor = db.execute('select * from players where id = ?',[myteamid['keeper']])
        keeper = cursor.fetchone()
    else:
        keeper = None
    if keeper!=None:
        if keeper['pos'] in ['WR','RB']:
            myTeam[keeper['pos']+'1'] = keeper['name']
        else:
            myTeam[keeper['pos']] = keeper['name']
    if request.method == 'POST':
        undo = request.form.get('undo')
        drafted = request.form.get('drafted')
        cursor = db.execute('select * from players where name = ?',[drafted])
        lastPick = cursor.fetchone()
        if lastPick!=None:
            lastPick = lastPick['id']
            cursor = db.execute('select * from picks where playerid = ?',[lastPick])
            pick = cursor.fetchone()
        else:
            cursor = db.execute('select * from picks where playerid is null')
            pick=cursor.fetchone()
        if pick== None:
            cursor = db.execute('select * from picks where playerid is null')
            pick = cursor.fetchone()
            db.execute('update picks set playerid = ? where no = ?',[lastPick,pick['no']])
            db.execute('delete from availablePlayers where playerid = ?',[lastPick])
            db.commit()
        if undo!=None:
            cursor = db.execute('select * from players where name = ?',[undo])
            undo = cursor.fetchone()
            db.execute('update picks set playerid = null where playerid = ?',[undo['id']])
            db.commit()
            cursor = db.execute('select * from picks where playerid not null')
            result = cursor.fetchall()
            draftedPlayers = []
            for person in result:
                draftedPlayers.append(person['playerid'])
            db.execute('drop table availablePlayers')
            db.execute('create table availablePlayers (rank integer, playerid integer references players(id),teamid references teams(id), name text, num integer, pos text, age integer, exp text, photo text,fav text)')
            db.commit()
            ranks = grabRanks()
            for rank in ranks[3]:
                if rank['playerid'] not in draftedPlayers:
                    player = getPlayer(rank['playerid'])
                    values = [rank['rank'],player['id'],player['teamid'],player['name'],player['num'],player['pos'],player['age'],player['exp'],player['photo'],player['fav']]
                    db.execute('insert into availablePlayers (rank, playerid, teamid, name, num, pos, age, exp, photo, fav) values (?,?,?,?,?,?,?,?,?,?)',values)
            db.commit()
            keepers=[]
            for team in teams:
                keepers.append(team['keeper'])
            cursor = db.execute('select * from picks where playerid not null')
            results = cursor.fetchall()
            cursor = db.execute('select * from picks where playerid is null')
            pick = cursor.fetchone()
            if pick['no']!=1:
                x=-1
                drafted = None
                while drafted==None:
                    if results[x]['playerid'] not in keepers:
                        drafted=getPlayer(results[x]['playerid'])['name']
                    else:
                        x=x-1
            else:
                drafted = None


        cursor = db.execute('select * from picks where playerid not null')
        playersDrafted = cursor.fetchall()
        x=0
        rb = {'rbpace':0,'rbdraft':0}
        wr = {'wrpace':0,'wrdraft':0}
        qb = {'qbpace':0,'qbdraft':0}
        te = {'tepace':0,'tedraft':0}
        while x<pick['no']:
            player=avgranks[x]
            cursor = db.execute('select * from players where id = ?',[player['playerid']])
            player = cursor.fetchone()
            if player['pos']=='RB':
                rb['rbpace']=rb['rbpace']+1
            elif player['pos']=='QB':
                qb['qbpace']=qb['qbpace']+1
            elif player['pos']=='WR':
                wr['wrpace']=wr['wrpace']+1
            else:
                te['tepace']=te['tepace']+1
            x=x+1
        for player in playersDrafted:
            cursor = db.execute('select * from players where id = ?',[player['playerid']])
            player = cursor.fetchone()
            if player['pos']=='RB':
                rb['rbdraft']=rb['rbdraft']+1
            elif player['pos']=='QB':
                qb['qbdraft']=qb['qbdraft']+1
            elif player['pos']=='WR':
                wr['wrdraft']=wr['wrdraft']+1
            else:
                te['tedraft']=te['tedraft']+1
        cursor = db.execute('select * from availablePlayers')
        availablePlayers = cursor.fetchall()
        cursor = db.execute('select * from picks where playerid is null')
        picks = cursor.fetchall()
        cursor = db.execute('select * from picks where teamid = ? and playerid not null',[myteamid['id']])
        mypicks = cursor.fetchall()
        if mypicks !=None:
            for pick in mypicks:
                cursor = db.execute('select * from players where id = ?',[pick['playerid']])
                player = cursor.fetchone()
                if player['name'] not in myTeam.values():
                    if player['pos'] in ['WR','RB']:
                        if myTeam[player['pos']+'1']=='':
                            myTeam[player['pos']+'1'] = player['name']
                        elif myTeam[player['pos']+'2']=='':
                            myTeam[player['pos']+'2'] = player['name']
                        elif myTeam['FLEX']=='':
                            myTeam['FLEX'] = player['name']
                        else:
                            myTeam['BENCH'].append(player['name'])
                    elif player['pos'] in ['QB','TE','DST','PK']:
                        if myTeam[player['pos']]=='':
                            myTeam[player['pos']]=player['name']
                        else:
                            myTeam['BENCH'].append(player['name'])
        if picks ==[]:
            return render_template("active_draft.html",availablePlayers=availablePlayers,picks=picks,teams=teams,avgranks=avgranks,espn=espn,fp=fp,cbs=cbs,nfl=nfl,qb=qb,rb=rb,wr=wr,te=te,pick='',myteam=myTeam)
        pickround = str((((picks[0]['no']-1)/len(teams)))+1).split('.')[0]
        pickno = (picks[0]['no']%len(teams))
        if pickno==0:
            pickno = len(teams)
        pick = 'Rd. '+pickround+' Pick '+str(pickno)
        return render_template("active_draft.html",availablePlayers=availablePlayers,picks=picks,teams=teams,avgranks=avgranks,espn=espn,fp=fp,cbs=cbs,nfl=nfl,qb=qb,rb=rb,wr=wr,te=te,pick=pick,myteam=myTeam,drafted=drafted)
    else:
        cursor = db.execute('select * from availablePlayers')
        availablePlayers = cursor.fetchall()
        cursor = db.execute('select * from picks where playerid is null')
        picks = cursor.fetchall()
        pick = 'Rd. 1 Pick 1'
        return render_template("active_draft.html",availablePlayers=availablePlayers,picks=picks,teams=teams,avgranks=avgranks,espn=espn,fp=fp,cbs=cbs,nfl=nfl,qb={},rb={},wr={},te={},pick=pick,myteam=myTeam)