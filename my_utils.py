import cx_Oracle
import pandas as pd
import requests
import random
from random import sample
from tqdm import tqdm

dsn = cx_Oracle.makedsn('',1521,'')
api_key = ''
riot_api_key = ''

def db_open():
    global db
    global cursor
    try:
        db = cx_Oracle.connect('scott','tiger',dsn)
        cursor = db.cursor()
        print('open!')
    except Exception as e:
        print(e)
        
def db_close():
    global db
    global cursor
    try:
        db.commit()
        cursor.close()
        db.close()
        print('close!')
    except Exception as e:
        print(e)

def sql_excute(q):
    global db
    global cursor
    try:
        if 'select' in q:
            df = pd.read_sql(sql=q, con=db)
            return df
        cursor.execute(q)
        return 'success!'
    except Exception as e:
        print(e)

def get_df(u):
    u = u.replace('(인증키)',api_key).replace('xml','json')
    res = requests.get(u).json()
    key = list(res.keys())[0]
    data = res[key]['row']
    df = pd.DataFrame(data)
    return df

def get_puuid(user):
    url = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/'+user+'?api_key='+riot_api_key
    res = requests.get(url).json()
    puuid = res['puuid']
    return puuid

def get_matchId(pId, num):
    url = 'https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/'+pId+\
    '/ids?api_key='+riot_api_key+'&start=0&count='+str(num)
    res = requests.get(url).json()
    return res

def get_matches_timelines(match_id):
    url = "https://asia.api.riotgames.com/lol/match/v5/matches/"+match_id+"?api_key="+riot_api_key
    res1 = requests.get(url).json()
    url = "https://asia.api.riotgames.com/lol/match/v5/matches/"+match_id+"/timeline?api_key="+riot_api_key
    res2 = requests.get(url).json()
    return res1, res2

# riot 데이터로부터 raw data 추출
def get_rawData(tier):
    tier_lst = ['I','II','III','IV']
    lst = []
    p = random.randrange(1,10)
    
    # riot api
    for t in tqdm(tier_lst):
        url='https://kr.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/'+tier+'/'+t+'?page='+str(p)+'&api_key='+riot_api_key
        res = requests.get(url).json()
        lst = lst+sample(res, 5)
    
    # summonerName
    print('get summonerName...')
    summonerName_lst = list(map(lambda x: x['summonerName'], lst))
    
    # puuid
    print('get puuid...')
    puuid_lst = []
    for n in tqdm(summonerName_lst):
        try:
            puuid_lst.append(get_puuid(n))
        except:
            continue
            
    # matchId
    print('get matchId...')
    matchId_lst = []
    for p in tqdm(puuid_lst):
        matchId_lst = matchId_lst+get_matchId(p, 2)
        
    # match, timeline
    print('get match & timeline...')
    tmp = []
    for m_id in tqdm(matchId_lst):
        tmp_lst = []
        tmp_lst.append(m_id)
        matches, timelines = get_matches_timelines(m_id)
        tmp_lst.append(matches)
        tmp_lst.append(timelines)
        tmp.append(tmp_lst)
    
    df = pd.DataFrame(tmp, columns = ['gameId','match','timeline'])
    print('complete!')
    return df

# match, timeline 데이터프레임 생성
def get_match_timeline_df(df):
    print('get matches & timelines...')
    match_lst = []
    timeline_lst = []
    for i in tqdm(range(len(df))):
        if df.iloc[i].match['info']['gameMode'] == 'CLASSIC':
            # matches
            for j in range(10):
                tmp = []
                tmp.append(df.iloc[i].gameId)
                tmp.append(df.iloc[i].match['info']['gameDuration'])
                tmp.append(df.iloc[i].match['info']['gameVersion'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['summonerName'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['summonerLevel'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['participantId'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['championName'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['champExperience'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['teamPosition'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['teamId'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['win'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['kills'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['deaths'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['assists'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['totalDamageDealtToChampions'])
                tmp.append(df.iloc[i].match['info']['participants'][j]['totalDamageTaken'])
                match_lst.append(tmp)
                
            # timelines
            for j in range(1, 11):
                tmp = []
                tmp.append(df.iloc[i].gameId)
                tmp.append(df.iloc[i].timeline['info']['frames'][0]['participantFrames'][str(j)]['participantId'])
                for k in range(5, 26):
                    try:
                        tmp.append(df.iloc[i].timeline['info']['frames'][k]['participantFrames'][str(j)]['totalGold'])
                    except:
                        tmp.append(0)
                timeline_lst.append(tmp)
            
    col = ['gameId','gameDuration','gameVersion','summonerName','summonerLevel','participantId','championName','champExperience',
           'teamPosition','teamId','win','kills','deaths','assists','totalDamageDealtToChampions','totalDamageTaken']
    m_df = pd.DataFrame(match_lst, columns=col).drop_duplicates()

    col = ['gameId','participantId','g_5','g_6','g_7','g_8','g_9','g_10','g_11','g_12','g_13','g_14','g_15','g_16','g_17',
           'g_18','g_19','g_20','g_21','g_22','g_23','g_24','g_25']
    t_df = pd.DataFrame(timeline_lst, columns=col).drop_duplicates()
    
    print('match_df length: ',len(m_df))
    print('timeline_df length: ',len(t_df))
    print('complete!')
    return m_df, t_df

# match데이터프레임 db에 넣기
def match_insert(row):
    query = (
        f'merge into match_data using dual on(gameId=\'{row.gameId}\' and participantId={row.participantId}) '
        f'when not matched then '
        f'insert (gameId, gameDuration, gameVersion, summonerName, summonerLevel, participantId, championName, champExperience, '
        f'teamPosition, teamId, win, kills, deaths, assists, totalDamageDealtToChampions, totalDamageTaken) '
        f'values(\'{row.gameId}\', {row.gameDuration}, '
        f'\'{row.gameVersion}\', \'{row.summonerName}\', {row.summonerLevel}, {row.participantId}, '
        f'\'{row.championName}\', {row.champExperience}, \'{row.teamPosition}\', {row.teamId}, '
        f'\'{row.win}\', {row.kills}, {row.deaths}, {row.assists}, '
        f'{row.totalDamageDealtToChampions}, {row.totalDamageTaken}) '        
    )
    mu.sql_excute(query)
    return

# timeline 데이터프레임 db에 넣기
def timeline_insert(row):
    query = (
        f'merge into timeline_data using dual on(gameId=\'{row.gameId}\' and participantId={row.participantId}) '
        f'when not matched then '
        f'insert (gameId, participantId, g_5, g_6, g_7, g_8, g_9, g_10, g_11, g_12, g_13, g_14, g_15, g_16, g_17, g_18, g_19, g_20, '
        f'g_21, g_22, g_23, g_24, g_25) values(\'{row.gameId}\', {row.participantId}, '
        f'{row.g_5}, {row.g_6}, {row.g_7}, {row.g_8}, {row.g_9}, {row.g_10}, {row.g_11}, {row.g_12}, {row.g_13}, {row.g_14}, {row.g_15}, '
        f'{row.g_16}, {row.g_17}, {row.g_18}, {row.g_19}, {row.g_20}, {row.g_21}, {row.g_22}, {row.g_23}, {row.g_24}, {row.g_25})'
    )
    mu.sql_excute(query)
    return

def set_format():
    from matplotlib import font_manager, rc
    font_path = "C:/Windows/Fonts/gulim.ttc"
    font = font_manager.FontProperties(fname=font_path).get_name()
    rc('font', family=font)
    return