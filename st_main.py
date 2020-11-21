from riotwatcher import LolWatcher, ApiError
from api_key import get_api_key
from matplotlib import  pyplot as plt

import os
from dotenv import load_dotenv

import pandas as pd
import streamlit as st
import seaborn as sns
import numpy as np
import matplotlib.ticker as ticker



def get_info():
    #global
    #load api key
    load_dotenv()
    api_key = os.getenv('api_key')
    watcher = LolWatcher(api_key)
    my_region = 'na1'
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
#get summoner name
my_name = st.text_input('What is your summoner name: ')
#when submit button is pressed
if st.button('Submit'):
    with st.spinner("Search ongoing"):
        #get info
        df = get_info()
        #title for padding
        st.title('\n')
        #begin graph dev
        #revise df for graphing
        df_revised = prep_df_for_barchart()
        #set plotsize
        fig, ax = plt.subplots(figsize=(7,10))
        #color palette
        palette = {"wins":"green","losses":"red"}
        #set sns font_scale
        sns.set(font_scale=1)
        #seaborn style
        #create
        sns.set_style("whitegrid")
        ax = sns.barplot(y="queue_type",x="Value",hue="Category",data=df_revised,palette=palette,orient="h")
        ax.set_xlabel('Count',fontsize=18)
        ax.set_ylabel('Queue Type',fontsize=18)
        ax.set_title('League of Legends - Season 13 Ranked Wins / Losses\n\n',fontsize=26)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(20))
        ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
        st.pyplot(fig)
        #done creation
        st.title('\n')
        #write df with win_loss_ratio
        df = get_win_loss_ratio_for_write_df(df)
        df.set_index(df.index,inplace=True)
        st.write(df)