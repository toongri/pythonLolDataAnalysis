import cx_Oracle
import pandas as pd
import requests
import random
from random import sample
from tqdm import tqdm
import time
import matplotlib.pyplot as plt
tqdm.pandas()

dsn = cx_Oracle.makedsn('localhost',1521,'xe')
api_key = ''
riot_api_key = 'RGAPI-cbbe428b-e159-4738-a1a9-3ae336e0335f'

def db_open():
    global db
    global cursor
    try:
        db = cx_Oracle.connect('toong','2579',dsn)
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
    '/ids?type=ranked&api_key='+riot_api_key+'&start=0&count='+str(num)
    res = requests.get(url).json()
    return res

def get_matches_timelines(match_id):
    url = "https://asia.api.riotgames.com/lol/match/v5/matches/"+match_id+"?api_key="+riot_api_key
    res1 = requests.get(url).json()
    url = "https://asia.api.riotgames.com/lol/match/v5/matches/"+match_id+"/timeline?api_key="+riot_api_key
    res2 = requests.get(url).json()
    return res1, res2

def get_user_name_list(tier):
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
    
    return summonerName_lst

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
            
    col = ['gameId','gameDuration','gameVersion','summonerName','summonerLevel','creatorId','championName','champExperience',
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

def get_matches(match_id):
    url = "https://asia.api.riotgames.com/lol/match/v5/matches/"+match_id+"?api_key="+riot_api_key
    res1 = requests.get(url).json()
    return res1


# match, timeline 데이터프레임 생성
def getTimeWardToongdf(df):
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
                
                
            gameLength = len(df.iloc[i].timeline['info']['frames'])
            for j in range(gameLength):
                if 'events' in list(df.iloc[i].timeline['info']['frames'][j].keys()):
                    eventLength = len(df.iloc[i].timeline['info']['frames'][j]['events'])
                    for k in range(eventLength):
                        if df.iloc[i].timeline['info']['frames'][j]['events'][k]['type'] == 'WARD_PLACED':
                            tmp = []
                            tmp.append(df.iloc[i].gameId)
                            tmp.append(df.iloc[i].timeline['info']['frames'][j]['events'][k]['creatorId'])
                            tmp.append(df.iloc[i].timeline['info']['frames'][j]['events'][k]['timestamp'])
                            timeline_lst.append(tmp)
                            
    col = ['gameId','gameDuration','gameVersion','summonerName','summonerLevel','creatorId','championName','champExperience',
           'teamPosition','teamId','win','kills','deaths','assists','totalDamageDealtToChampions','totalDamageTaken']
    m_df = pd.DataFrame(match_lst, columns=col).drop_duplicates()
    
    col = ['gameId','creatorId','timestamp']
    t_df = pd.DataFrame(timeline_lst, columns=col).drop_duplicates()
    
    print('match_df length: ',len(m_df))
    print('timeline_df length: ',len(t_df))
    print('complete!')
    return m_df, t_df


# match데이터프레임 db에 넣기
def matchToongInsert(row):
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
            
    col = ['gameId','gameDuration','gameVersion','summonerName','summonerLevel','creatorId','championName','champExperience',
           'teamPosition','teamId','win','kills','deaths','assists','totalDamageDealtToChampions','totalDamageTaken']
    m_df = pd.DataFrame(match_lst, columns=col).drop_duplicates()

    col = ['gameId','participantId','g_5','g_6','g_7','g_8','g_9','g_10','g_11','g_12','g_13','g_14','g_15','g_16','g_17',
           'g_18','g_19','g_20','g_21','g_22','g_23','g_24','g_25']
    t_df = pd.DataFrame(timeline_lst, columns=col).drop_duplicates()
    
    print('match_df length: ',len(m_df))
    print('timeline_df length: ',len(t_df))
    print('complete!')
    return m_df, t_df


# match, timeline 데이터프레임 생성
def getTimeWardToongdf(df):
    print('get matches & timelines...')
    match_lst = []
    timeline_lst = []
    for i in tqdm(range(len(df))):
        if 'info' in list(df.iloc[i].match.keys()):
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

                if 'info' in list(df.iloc[i].timeline.keys()):
                    gameLength = len(df.iloc[i].timeline['info']['frames'])
                    for j in range(gameLength):
                        if 'events' in list(df.iloc[i].timeline['info']['frames'][j].keys()):
                            eventLength = len(df.iloc[i].timeline['info']['frames'][j]['events'])
                            for k in range(eventLength):
                                if df.iloc[i].timeline['info']['frames'][j]['events'][k]['type'] == 'WARD_PLACED':
                                    tmp = []
                                    tmp.append(df.iloc[i].gameId)
                                    tmp.append(df.iloc[i].timeline['info']['frames'][j]['events'][k]['creatorId'])
                                    tmp.append(df.iloc[i].timeline['info']['frames'][j]['events'][k]['timestamp'])
                                    timeline_lst.append(tmp)
                            
    col = ['gameId','gameDuration','gameVersion','summonerName','summonerLevel','creatorId','championName','champExperience',
           'teamPosition','teamId','win','kills','deaths','assists','totalDamageDealtToChampions','totalDamageTaken']
    m_df = pd.DataFrame(match_lst, columns=col).drop_duplicates()
    
    col = ['gameId','creatorId','timestamp']
    t_df = pd.DataFrame(timeline_lst, columns=col).drop_duplicates()
    
    print('match_df length: ',len(m_df))
    print('timeline_df length: ',len(t_df))
    print('complete!')
    return m_df, t_df

def toong(tier):
    raw_data = get_rawData(tier)
    match_df, timeline_df = getTimeWardToongdf(raw_data)
    timeline_df = timeline_df[timeline_df['creatorId']>0]
    timeline_df.groupby(['gameId', 'creatorId']).size()
    group_timeline_df = pd.DataFrame(timeline_df.groupby(['gameId', 'creatorId']).size().reset_index(name = 'count'))
    all_df = pd.merge(left=group_timeline_df, right=match_df, how='left', on=['gameId','creatorId'], sort=False)
    all_df.rename(columns={'count':'cnt'}, inplace = True)
    all_df = all_df[all_df['gameDuration']<7000]
    all_df = all_df.dropna(axis=0)
    return all_df

# match데이터프레임 db에 넣기
def matchToongInsert(row):
    query = (
        f'merge into toong_match using dual on(gameId=\'{row.gameId}\' and creatorId={row.creatorId}) '
        f'when not matched then '
        f'insert (gameId, creatorId, cnt, gameDuration, gameVersion, summonerName, summonerLevel, championName, champExperience, '
        f'teamPosition, teamId, win, kills, deaths, assists, totalDamageDealtToChampions, totalDamageTaken) '
        f'values(\'{row.gameId}\', {row.creatorId}, {row.cnt}, {row.gameDuration}, '
        f'\'{row.gameVersion}\', \'{row.summonerName}\', {row.summonerLevel}, '
        f'\'{row.championName}\', {row.champExperience}, \'{row.teamPosition}\', {row.teamId}, '
        f'\'{row.win}\', {row.kills}, {row.deaths}, {row.assists}, '
        f'{row.totalDamageDealtToChampions}, {row.totalDamageTaken}) '
    )
    sql_excute(query)
    return

def data_insert(tier):
    
    # api 사용하여 raw data 수집
    # raw data 사용하여 match, timeline dataframe 생성
    df = toong(tier)

    # match, timeline dataframe db insert
    db_open()
    df.progress_apply(lambda x: matchToongInsert(x), axis=1)
    db_close()
    print('complete!')

def data_long_insert(tier, n):
    for i in range(n):
        # api 사용하여 raw data 수집
        # raw data 사용하여 match, timeline dataframe 생성
        df = toong(tier)

        # match, timeline dataframe db insert
        db_open()
        df.progress_apply(lambda x: matchToongInsert(x), axis=1)
        db_close()
        print(i, ' complete!')
        time.sleep(100)
        
        
def createTable():
    query = """
    create table toong_match(gameId varchar(50),creatorId number(20), cnt number(20), gameDuration varchar(50), gameVersion varchar(50), 
    summonerName varchar(50), summonerLevel number(20),championName varchar(50), champExperience number(20),
    teamPosition varchar(50), teamId number(20), win varchar(50), kills number(20), deaths number(20), assists number(20),
    totalDamageDealtToChampions number(20), totalDamageTaken number(20),
    constraint pk_id_crtid primary key(gameId, creatorId))
     """

    db_open()
    res = sql_excute(query)
    db_close()
    res
    
def xyreturn():
    db_open()
    match_df = sql_excute('select * from toong_match')
    db_close()

    match_df = match_df[['CREATORID', 'CNT', 'WIN']]
    list_vic_rate = []
    list_ward_size = []
    x_list = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 43, 45, 47, 49, 53, 57, 60, 70, 80]
    n_match_df = match_df[match_df['CNT'] <= x_list[0]]
    len_n_match_df = len(n_match_df)
    len_vic_n_match_df = len(n_match_df[n_match_df['WIN'] == 'True'])
    win_per = len_vic_n_match_df/len_vic_n_match_df* 100 if len_n_match_df != 0 else 0
    list_vic_rate.append(win_per)
    list_ward_size.append(x_list[0])


    for i in range(1, len(x_list)):
        n_match_df = match_df[(match_df['CNT'] <= x_list[i]) & (match_df['CNT'] > x_list[i - 1])]
        len_n_match_df = len(n_match_df)
        len_vic_n_match_df = len(n_match_df[n_match_df['WIN'] == 'True'])
        win_per = len_vic_n_match_df/len_vic_n_match_df* 100 if len_n_match_df != 0 else 0
        list_vic_rate.append(win_per)
        list_ward_size.append(x_list[i - 1] + 1)

    n_match_df = match_df[match_df['CNT'] > x_list[-1]]
    len_n_match_df = len(n_match_df)
    len_vic_n_match_df = len(n_match_df[n_match_df['WIN'] == 'True'])'])
    win_per = len_vic_n_match_df/len_vic_n_match_df* 100 if len_n_match_df != 0 else 0
    list_vic_rate.append(win_per)
    list_ward_size.append(x_list[-1] + 1)
    
    return list_ward_size, list_vic_rate

def set_format():
    from matplotlib import font_manager, rc
    font_path = "C:/Windows/Fonts/gulim.ttc"
    font = font_manager.FontProperties(fname=font_path).get_name()
    rc('font', family=font)
    return

def createPlot(x,y):
    set_format()
    plt.plot(x, y, '.', label='승률(%)')
    plt.xlabel('와드 개수 (개)')
    plt.title('와드 개수에 따른 승률', pad=20)
    plt.legend()