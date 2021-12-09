from django.shortcuts import render

from .forms import UserSearchForm, ActivateTweetStreamerForm, TweetSubjectSentimentForm

import plotly.graph_objs as go
from plotly.offline import plot
from wordcloud import WordCloud
from textblob import TextBlob
import matplotlib.pyplot as plt
from datetime import datetime

import random
import sqlite3, sqlalchemy
import pandas as pd
import numpy as np

from media_effectiveness import main, news_scraper, bot

# Create your views here.
def home(request):
    """
    Not really much going on here except the base template
    and we activate the bot
    """
    bot.bot_thread.start()
        
            
    return render(request, "displayer/display.html")

def twitter(request):
    """
    Where we mess with twitter data. Ask for whatever you want.
    """
    
    user_form = UserSearchForm()
    tweet_keyword_form = ActivateTweetStreamerForm()
    subject_form = TweetSubjectSentimentForm()
    
    context = {"user_form": user_form,
               "tweet_keyword_form": tweet_keyword_form,
               "subject_form": subject_form}
    
    engine = sqlalchemy.create_engine("sqlite:////home/main/Documents/Main/Code/Python/Data/web_displayer/sent_data.db") 
    df = pd.read_sql("tweet_data", engine)
    
    user_list = []
    for author in df['author']:
        if author not in user_list:
            user_list.append(author)
            
            
    if request.method == "POST" and "userformbtn" in request.POST:
        form = UserSearchForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            numtweets = form.cleaned_data['numtweets']
            print(user)
            # make the users name into a twitter username
            search_username = user.replace(" ", "")
            search_username = search_username.lower()
            main.get_user_tweets(search_username, numtweets)
            
            # get the users data
            engine2 = sqlalchemy.create_engine("sqlite:////home/main/Documents/Main/Code/Python/Data/web_displayer/sent_data.db") 
            tweet_df = pd.read_sql("tweet_data", engine2)
            user_tweets = tweet_df.loc[tweet_df['author'] == user]
            print("TWEET DF:")
            print(user_tweets.head())
            
            # create the chart
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=user_tweets['DTG'], y=user_tweets['likes'], mode="lines+markers",name=user))
            fig2.update_layout(title="Tweet likes", xaxis_title="Date", yaxis_title="Likes")
            fig2.update_layout(template='plotly_dark', title=f"{user} tweet likes over time")
            
            # put chart on the page
            chart_div = plot(fig2, output_type='div')
            context['userchart'] = chart_div
            
            user_tweets = tweet_df.loc[tweet_df['subject'] == 'gretathunberg']
            print("TWEET DF:")
            print(user_tweets.head())
            
            return render(request, "displayer/twitter.html", context)
        
    # where we search for tweets by chosen keywords and then see some sentiment data
    elif request.method == "POST" and "tweetkeywordbtn" in request.POST:
        form = ActivateTweetStreamerForm(request.POST)
        if form.is_valid():
            keywords = form.cleaned_data['keywords'].split(" ")
            duration = form.cleaned_data['duration']
            print(keywords)
            print(duration)
            main.get_keyword_tweets(keywords, duration)
            context['table'] = True
            
            
            engine = sqlalchemy.create_engine("sqlite:////home/main/Documents/Main/Code/Python/Data/web_displayer/sent_data.db") 
            tweet_df = pd.read_sql("tweet_data", engine)
            
            
            # display basic polarity and subjectivity
            data = pd.read_pickle("corpus.pkl")
            users = []
            for user in data.columns:
                users.append(user)
            user_data_df = pd.DataFrame(index=users, columns=['polarity','subjectivity'])
            test_dict = {}

            for user in users:
                polarities = []
                subjectivities = []
                cell=0
                test_dict[user] = {}
                test_dict[user]['pol'] = []
                test_dict[user]['sub'] = []
                for tweet in data[user]:
                    polarities.append(TextBlob(str(tweet)).sentiment.polarity)
                    subjectivities.append(TextBlob(str(tweet)).subjectivity)
                    
                    test_dict[user]['pol'].append(TextBlob(str(tweet)).sentiment.polarity)
                    test_dict[user]['sub'].append(TextBlob(str(tweet)).subjectivity)
                    
                polarity = np.mean(np.array(polarities))
                subjectivity = np.mean(np.array(subjectivities))
                
                    
                user_data_df['polarity'][user] = polarity
                user_data_df['subjectivity'][user] = subjectivity


            sentdata = {}
            sentdata['polarity'] = np.mean(user_data_df['polarity'])
            sentdata['subjectivity'] = np.mean(user_data_df['subjectivity'])
            sentdata['date'] = datetime.now()
            
            sentdata = pd.DataFrame.from_dict(sentdata, orient="index")
            sentdata = sentdata.transpose()

            context['pol'] = np.mean(user_data_df['polarity'])
            context['sub'] = np.mean(user_data_df['subjectivity'])
            sentdata.to_sql("sent_over_time", engine, if_exists="append", index=True)
            
            # chart the sentiment over time
            sentdata = pd.read_sql("sent_over_time", engine)
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=sentdata['date'], y=sentdata['polarity'], mode="lines+markers",name=user))
            fig2.update_layout(title="Polarity over time", xaxis_title="Date", yaxis_title="Polarity")
            fig2.update_layout(template='plotly_dark', title=f"Topic polarity over time")
            
            # put chart on the page
            chart_div = plot(fig2, output_type='div')
            context['userchart'] = chart_div
            
            return render(request, "displayer/twitter.html", context)
        
    elif request.method == "POST" and "subjectbtn" in request.POST:
        form = TweetSubjectSentimentForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            print(subject)
            
            engine = sqlalchemy.create_engine("sqlite:////home/main/Documents/Main/Code/Python/Data/web_displayer/sent_data.db") 
            tweet_df = pd.read_sql("tweet_data", engine)
            user_tweets = tweet_df.loc[tweet_df['subject'] == subject]
            print("TWEET DF:")
            print(user_tweets.head())
            
            
            data = pd.read_pickle("corpus.pkl")
            users = []
            for user in data.columns:
                users.append(user)
            
            wc = WordCloud(stopwords=main.stop_words(), background_color="white", colormap="Dark2", max_font_size=150, random_state=42)
            plt.rcParams['figure.figsize'] = [16,6]
            data = pd.read_pickle("document_term_matrix.pkl")
            data = data.transpose()
            data_clean = pd.read_pickle("Cleaned_corpus.pkl")
            i = 0
            for index, user in enumerate(data.columns):
                wc.generate(data_clean[user])
                
                plt.subplot(3,4,1)
                plt.imshow(wc, interpolation="bilinear")
                plt.axis("off")
                plt.title(user)
                plt.savefig(f"wordcloud.png")
                i += 1
            
            
            return render(request, "displayer/twitter.html", context)
        
    return render(request, "displayer/twitter.html", context)
