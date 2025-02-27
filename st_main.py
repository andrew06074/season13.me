import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


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

from PIL import Image
#load css
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
local_css("style.css")

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

def main():
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
            win_loss_row['Wins'] = row['wins']
            win_loss_row['Losses'] = row['losses']
            win_loss.append(win_loss_row)
        #create df from data
        df = pd.DataFrame(win_loss)
        #replace string values
        df['queue_type'] = df['queue_type'].str.replace('RANKED_SOLO_5x5','Ranked Solo / Duo')
        df['queue_type'] = df['queue_type'].str.replace('RANKED_FLEX_SR','Ranked Flex')
        return df
    
    def prep_df_for_barchart():
        #create win df
        win_df = df.drop('Losses', axis=1)\
            .rename(columns={'Wins': 'Value'})\
            .merge(pd.DataFrame({'Category': list(pd.np.repeat('Wins',len(df)))}),
            left_index=True,
            right_index=True)
        #create loss df
        loss_df = df.drop('Wins', axis=1)\
            .rename(columns={'Losses': 'Value'})\
            .merge(pd.DataFrame({'Category': list(pd.np.repeat('Losses',len(df)))}),
            left_index=True,
            right_index=True)
        #concat the new dfs
        df_revised = pd.concat([win_df,loss_df])
        return df_revised

    #take df and calcualte win rate column, return new df-df with re-named columns
    def get_win_loss_ratio_for_write_df(df):
        #create win / loss ratio
        df['win_loss_ratio'] = df['Wins'] / (df['Wins'] + df['Losses'])
        #rename
        df.columns = ['Queue Type','Wins','Losses','Win Rate']
        return df
    
    def plot_top_15_pie():
        #get last 100 champs played
        count = get_last_100_champs_played()
        #top 10 for better pieplot formating
        count = count.head(15)
        labels = count.keys()
        #set seaborn color pallette
        colors = sns.color_palette("tab10")
        #set figsize
        pie,ax = plt.subplots(figsize=[4,4])
        #pie chart labels white
        mpl.rcParams['text.color'] = 'w'
        #create pie
        plt.pie(x=count,labels=labels,textprops={'fontsize':10  },colors=colors)
        #set pie title
        ax.set_title(my_name + ' - Top 15 Champions Played - Season 13' + '\n',fontsize=16,color='white')
        #set pie background to same hex as main background
        pie.set_facecolor('#30394b')
        #plot pie
        st.pyplot(pie)
        #create count dataframe for display
        count = count.reset_index(name='counts')
        #rename count datafram columns
        count.columns = ['Champion Name','Number of Games']
        #set index to champion name
        count.set_index('Champion Name', inplace=True)
        #return count as dataframe-count
        return count
   
    def plot_wins_losses(df):
        #begin graph dev
        #revise df for graphing
        df_revised = prep_df_for_barchart()
        #set plotsize
        fig, ax = plt.subplots(figsize=(10,5))            
        #set sns font_scale
        sns.set(font_scale=2)
        #create
        ax = sns.barplot(y="queue_type",x="Value",hue="Category",data=df_revised,orient="h",alpha=1,palette=sns.color_palette('tab10', n_colors=5))
        #dont show x label
        ax.set_xlabel('')
        #dont show y label
        ax.set_ylabel('')
        #set barplot title and title params here
        ax.set_title(my_name + ' - Ranked Wins / Losses - Season 13'+'\n',fontsize=48,color='white')
        #custom ticks and scaler for plot
        ax.xaxis.set_major_locator(ticker.MultipleLocator(20))
        ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
        #change tick params
        ax.tick_params(axis='y', which='major', labelsize=28, labelcolor='white')
        ax.tick_params(axis='x', which='major', labelsize=17,labelcolor='white')
        #turn off grid
        ax.grid(False)
        #remove legend background
        ax.legend(frameon=False,labelcolor='white')
        #background color for chart
        ax.set_facecolor('#30394b')
        fig.set_facecolor('#30394b')
        #plot
        st.pyplot(fig)
        #format for table write
        df['w_l'] = df['Wins'] / (df['Losses'] + df['Wins'])
        df.columns = ['Queue Type','Wins','Losses','Win Rate']
        df.set_index('Queue Type', inplace=True)
        #write df
        df = df.style.set_properties(**{'color': 'white',
                        'border-color': 'white',})
        return df

    #PAGE IS PRITED HERE
    logo= Image.open('logo.png')
    st.image(logo)
    st.markdown("<h1 style='text-align: center'>season13.me</h1>", unsafe_allow_html=True)
    st.title('\n')
    st.title('\n')
    st.title('\n')
    st.title('\n')
    st.title('\n')
    st.title('\n')
    st.markdown("<h3 style='text-align: center'>Search for summoner</h3>", unsafe_allow_html=True)
    my_name = st.text_input('','Scarra')
    #when submit button is pressed
    if st.button('Submit'):
        with st.spinner("Search ongoing"):
            try:
                st.title('\n')
                st.title('\n')
                st.markdown("<hr></hr>",unsafe_allow_html=True)
                st.title('\n')
                #get info
                df = get_info()
                #title for padding
                st.title('\n')
                st.title('\n')
                #pie plot
                count = plot_top_15_pie()
                #table header
                st.header('Champion by times played')
                #table
                st.write(count)
                #formating
                st.title('\n')
                st.markdown("<hr></hr>",unsafe_allow_html=True)
                st.title('\n')
                #win_loss_plot
                win_loss = plot_wins_losses(df)
                st.title('\n')
                st.header('Wins and losses with win rate')
                st.write(win_loss)
                #footer
            except:
                st.title('Try another name!')
                st.subheader('Player name must be in na1 region')
                st.subheader('Make sure playername is spelled correctly')
    st.title('\n')
    st.title('\n')
    st.title('\n')
    st.markdown("<h5 style='text-align: center'>@hancockdevelop</h1>", unsafe_allow_html=True)
                
main()