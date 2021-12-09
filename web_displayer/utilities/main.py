try:
    import tweet_getter, news_scraper
except:
    # when using django
    from . import tweet_getter
import numpy as np
import pandas as pd
import sqlite3, sqlalchemy
import re, time

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import text
import pickle
from collections import Counter

"""
This is the main 'utility' file that
Its functions can be called from the django application/other modules
It then routes the command to other utility scripts (news scraper/tweet_getter)
"""

def clean(data):
    """
    Use regex (yuck) to clean up strings
    """
    try:
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", data).split())
    except:
        data = str(data)
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", data).split())

# ==========DATA GATHERING==========
def get_user_tweets(user, num):
    """
    Get tweets and store to tweet_data table
    using the tweepy library to connect to twitter API
    """
    twitter_client = tweet_getter.TwitterClient()
    api = twitter_client.get_twitter_client_api()

    tweets = api.user_timeline(screen_name=user, count=int(num))
    tweet_analyzer = tweet_getter.TweetAnalyzer()

    return tweet_analyzer.tweets_to_df(tweets, user)
    
def get_keyword_tweets(keywords: list, listen_time: int):
    """
    Get tweets containing a particular keyword/s on command
    using the tweepy Stream class
    """
    listener = tweet_getter.TweetStreamer()
    listener.stream_tweets("tweetstore.json", keywords, listen_time)
    
    
def get_news(searchterm):
    news_scraper.scraper(searchterm)
    
    
# ==========Data Preparation==========
"""
These functions are to be run when the dataset is updated
This can be done via the dashboard
"""

def get_authors():
    conn=sqlite3.connect("sent_data.db")
    cur=conn.cursor()
    cur.execute("SELECT author FROM tweet_data")
    result=cur.fetchall()
    conn.close()
    return result

def get_tweets_by_author(author):
    conn=sqlite3.connect("sent_data.db")
    cur=conn.cursor()
    cur.execute("SELECT tweets FROM tweet_data WHERE author=?", (author,))
    result=cur.fetchall()
    conn.close()
    return result

def remove_common_words():
    data = pd.read_pickle("document_term_matrix.pkl")
    data = data.transpose() # flips the dataframe - this makes the aggregations easier...its harder to do things across rows than it is across columns
    print(data.head())
    print("+")
    time.sleep(2)
    top_dict = {}
    for c in data.columns:
        top = data[c].sort_values(ascending=False).head(30)
        top_dict[c] = list(zip(top.index, top.values))
    
    # separate by user
    for user, top_words in top_dict.items():
        print(user)
        print(", ".join([word for word, count in top_words[0:20]]))
        print("===")
    words = []
    for user in data.columns:
        top = [word for (word, count) in top_dict[user]]
        for t in top:
            words.append(t)
    
    add_stop_words = [word for word, count in Counter(words).most_common() if count >= len(data.columns)]
    data_clean = pd.read_pickle("Cleaned_corpus.pkl")

    stop_words = text.ENGLISH_STOP_WORDS.union(add_stop_words) # adds the new stop word list

    # recreate the DTM
    cv = CountVectorizer(stop_words=stop_words)
    data_cv = cv.fit_transform(data_clean) # the cleaned tweets (which we saved over the original df hence its still just called df)
    data_stop = pd.DataFrame(data_cv.toarray(), columns=cv.get_feature_names()) # converts to an array and labels the columns
    data_stop.index = data_clean.index
    
    # save as pickle files
    pickle.dump(cv, open("cv_stop.pkl", "wb"))
    data_stop.to_pickle("dtm_stop.pkl")


def prepare_tweet_data():
    """
    Goes over the database (which may have been updated since this function was last called)
    and creates new corpuses to be used by the views for displaying the more up to date data
    """
    authors = {clean(a) for a in get_authors()}
    print(authors)

    tweets_to_author = {}
    for author in authors:
        tweets_to_author[author] = [t for t in get_tweets_by_author(author)]
    print(tweets_to_author)
    print("=======--========")



    dict_df = pd.DataFrame.from_dict(tweets_to_author, orient="index")
    dict_df.to_pickle("corpus.pkl") # make a new one, overwrite...
    cleaned_df = dict_df.apply(clean)
    cleaned_df.to_pickle("Cleaned_corpus.pkl")
    
    cv = CountVectorizer(stop_words="english")
    data_cv = cv.fit_transform(cleaned_df) # the cleaned tweets (which we saved over the original df hence its still just called df)
    df_document_term_matrix = pd.DataFrame(data_cv.toarray(), columns=cv.get_feature_names()) # converts to an array and labels the columns
    df_document_term_matrix.index = cleaned_df.index
    df_document_term_matrix.to_pickle("document_term_matrix.pkl")
    print(dict_df.head()) 
    print("=================")
    remove_common_words()
    return dict_df

def stop_words():
    """
    Simply to get the stop words from another file
    """
    return text.ENGLISH_STOP_WORDS


if __name__ == '__main__':
    # if running manually
    prepare_tweet_data()
    