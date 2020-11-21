from riotwatcher import LolWatcher, ApiError
from matplotlib import  pyplot as plt

import os
from dotenv import load_dotenv

import pandas as pd
import streamlit as st
import seaborn as sns
import numpy as np
import matplotlib.ticker as ticker
import matplotlib as mpl

#authenticate with riot api activate lol watcher and set region to na1
#global
#load api key
load_dotenv()
#local key
#api_key = os.getenv('api_key')
#heroku key
api_key = os.environ.get('api_key')
watcher = LolWatcher(api_key)
#set region to na1
my_region = 'na1'

def get_last_100_champs_played():
    #get summoner id, needed to get matchlost
    me = watcher.summoner.by_name(my_region,my_name)
    #get matchlist
    my_matches = watcher.match.matchlist_by_account(my_region,me['accountId'])
    #get each champion played from last 100 games
    #create blank list to store matchlist in
    match_list = []
    #returns last 100 champions as id, change id to name with Data Dragon
    for row in my_matches['matches']:
        match_list_row = {}
        match_list_row['champion'] = row['champion']
        match_list.append(match_list_row)
    #get latest league version
    latest = watcher.data_dragon.versions_for_region(my_region)['n']['champion']
    #get list of champion names from Data Dragon
    champ_list = watcher.data_dragon.champions(latest,False,'en_US')
    #blank dict for champin names and keys
    champ_dict = {}
    #load dict of champion names and ids as keys
    for key in champ_list['data']:
        row = champ_list['data'][key]
        champ_dict[row['key']] = row['id']
    #change id to champion name
    for row in match_list:
        row['championName'] = champ_dict[str(row['champion'])]
    #create df from match list
    df = pd.DataFrame(match_list)
    #count number of occurances for each champion played
    count = df.value_counts(df['championName'])

    return count

def get_info():
    #get summoner Id
    me = watcher.summoner.by_name(my_region,my_name)
    #get ranked stats
    my_ranked_stats = watcher.league.by_summoner(my_region,me['id'])
    #create dataframe
    win_loss = []
    for row in my_ranked_stats:
        win_loss_row = {}
        win_loss_row['queue_type'] = row['queueType']
        win_loss_row['wins'] = row['wins']
        win_loss_row['losses'] = row['losses']
        win_loss.append(win_loss_row)
    #create df from data
    df = pd.DataFrame(win_loss)
    #replace string values
    df['queue_type'] = df['queue_type'].str.replace('RANKED_SOLO_5x5','Ranked Solo / Duo')
    df['queue_type'] = df['queue_type'].str.replace('RANKED_FLEX_SR','Ranked Flex')
    return df

def prep_df_for_barchart():
    #create win df
    win_df = df.drop('losses', axis=1)\
        .rename(columns={'wins': 'Value'})\
        .merge(pd.DataFrame({'Category': list(pd.np.repeat('wins',len(df)))}),
        left_index=True,
        right_index=True)
    #create loss df
    loss_df = df.drop('wins', axis=1)\
        .rename(columns={'losses': 'Value'})\
        .merge(pd.DataFrame({'Category': list(pd.np.repeat('losses',len(df)))}),
        left_index=True,
        right_index=True)
    #concat the new dfs
    df_revised = pd.concat([win_df,loss_df])
    return df_revised

def get_win_loss_ratio_for_write_df(df):
    #create win / loss ratio
    df['win_loss_ratio'] = df['wins'] / (df['wins'] + df['losses'])
    #rename
    df.columns = ['Queue Type','Wins','Losses','Win Rate']
    return df

#USER INTERACTION HERE
st.write('@hancockdevelop')
#get summoner name
st.title('Search for summoner name: ')
my_name = st.text_input('','Scarra')
#when submit button is pressed
if st.button('Submit'):
    with st.spinner("Search ongoing"):
        #get info
        df = get_info()
        #title for padding
        st.title('\n')
        st.title('\n')
        st.title('\n')
        st.title('\n')
        #begin graph dev
        #revise df for graphing
        df_revised = prep_df_for_barchart()
        #set plotsize
        fig, ax = plt.subplots(figsize=(10,5))
        #color palette
        palette = {"wins":"green","losses":"red"}
        #set sns font_scale
        sns.set(font_scale=2)
        sns.set_style("white")
        #create
        ax = sns.barplot(y="queue_type",x="Value",hue="Category",data=df_revised,palette=palette,orient="h")
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_title(my_name + ' - Ranked Wins / Losses - Season 13'+'\n',fontsize=38)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(20))
        ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
        #change tick params
        ax.tick_params(axis='y', which='major', labelsize=28)
        ax.tick_params(axis='x', which='major', labelsize=17)
        ax.grid(False)
        st.pyplot(fig)
        #format for table write
        df['w_l'] = df['wins'] / (df['losses'] + df['wins'])
        df.columns = ['Queue Type','Wins','Losses','Win Rate']
        df.set_index('Queue Type', inplace=True)
        st.table(df)
        #done creation
        st.title('\n')
        st.title('\n')
        #pie plot
        #get last 100 champs played
        count = get_last_100_champs_played()
        #top 10 for better pieplot formating
        count = count.head(15)
        labels = count.keys()
        #set pieplot params
        colors = sns.color_palette("tab10")
        pie,ax = plt.subplots(figsize=[4,4])
        plt.pie(x=count,labels=labels,textprops={'fontsize':10  },colors=colors)
        ax.set_title(my_name + ' - Top 10 Champions Played - Season 13' + '\n',fontsize=12)
        st.pyplot(pie)
        count = count.reset_index(name='counts')
        count.columns = ['Champion Name','Number of Games']
        count.set_index('Champion Name', inplace=True)
        st.table(count)