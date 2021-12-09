import tweepy, time
import pandas as pd
import numpy as np
import ast, json, re, sqlalchemy
import matplotlib.pyplot as plt
from textblob import TextBlob

from dateutil.parser import parse, parserinfo
try:
    # only when running manually/testing
    import keys 
except:
    # when using django
    from . import keys

class CustomParserInfo(parserinfo):
    """
    This is for saving dates as datetime objects
    """
    DAYS = list(range(1, 31))
    MONTHS = [("Jan", "January"), ("Feb", "February"), ("Mar", "March"), ("Apr", "April"), ("May", "May"), ("Jun", "June"), ("Jul", "July"), ("Aug", "August"), ("Sep", "September"), ("Oct", "October"), ("Nov", "November"), ("Dec", "December"),]
    YEARS = list(range(2020, 2050))

class TwitterClient():
    """
    A client to browse twitter programmatically with tweepy
    """
    
    def __init__(self, twitter_user=None):
        self.auth = Authenticator().authenticate()
        self.twitter_client = tweepy.API(self.auth)
        self.twitter_user = twitter_user # the user whose tweets to watch - defaults to None ie YOU/ME if none is
        
    def get_twitter_client_api(self):
        """
        Gets the twitter client to be used elsewhere (helps with auth)
        """
        return self.twitter_client
        
    def get_user_timeline_tweets(self, num_tweets):
        """
        The "cursor" goes over the user's timeline and gets up to num_tweets specified
        If you don't specify a user it defaults to you (user logged in on the API)
        """
        tweets = []
        
        for tweet in tweepy.Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets
    
    def get_friend_list(self, num_friends):
        friends = []
        for friend in tweepy.Cursor(self.twitter_client.get_friends, id=self.twitter_user).items(num_friends):
            friends.append(friend)
        return friends
    
    def get_home_timeline_tweets(self, num_tweets):
        """
        These are the ones on your homepage from people you follow
        """
        home_timeline_tweets = []
        for tweet in tweepy.Cursor(self.twitter_client.home_timeline, id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets

class Authenticator():
    """
    Use to log in to twitter. Returns the auth object that other classes/etc can use to auth.
    """
    
    def authenticate(self):
        auth = tweepy.OAuthHandler(keys.API_KEY, keys.API_SECRET)
        auth.set_access_token(keys.ACCESS_TOKEN, keys.ACCESS_TOKEN_SECRET)
        return auth
   
class TweetStreamer():
    """
    Configures the tweetlistener class to stream tweets with the desired keyword filters
    """
    
    def __init__(self):
        self.auth = Authenticator().authenticate()
        print("Tweet streamer is logged in")
    
    def stream_tweets(self, store_file, htag_list, listen_time):
        stream = TweetListener(store_file, self.auth.consumer_key, self.auth.consumer_secret, self.auth.access_token, self.auth.access_token_secret, htag_list[0])
        print(f"stored tweets to {store_file}")
        stream.filter(track=htag_list, threaded=True)
        time.sleep(listen_time)
        stream.disconnect()
        
        

class TweetListener(tweepy.Stream):
    """
    Streams the tweets for the specified duration and stores them to the database.
    Inherits from the Stream class, with the added param of the file to store the tweets to
    (that's what super is doing)
    Except store_file is now 'deprecated' and I'm saving to the database...
    """
    
    def __init__(self, store_file, consumer_key, consumer_secret, access_token, access_token_secret, subject):
        super(TweetListener, self).__init__(consumer_key, consumer_secret, access_token, access_token_secret)
        self.store_file = store_file
        self.subject = subject
        print(f"tweet listener is ready to store files to {store_file}")
    
    def on_data(self, data):
        """
        Upon receipt of a tweet do this
        """
        tweets = []
        try:
            data = data.decode()
            data = json.loads(data)
            tweets.append(data)
            self.save_to_df(data)
            return True
        except Exception as e:
            print(f"error: {e}")
        return False
    
    def on_error(self, status):
        print(f"error!! {status}")
        if status == 420:
            return False 
        
    
    def clean_tweet(self, tweet):
        try:
            return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())
        except:
            tweet = str(tweet)
            return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet):
        """
        Uses textblob to get a polarity score
        Subjectivity scores were not working well with tweets so excluded
        """
        analysis = TextBlob(self.clean_tweet(tweet))
        if analysis.sentiment.polarity > 0:
            return 1 # positive tweet, happy days
        elif analysis.sentiment.polarity == 0:
            return 0 # dunno. meh.
        else:
            return -1 # must be a bit of a dick
        
    def save_to_df(self, t):
        """
        Saves collected tweets as a df that is then passed to the DB
        """
        tweettime = parse(t['created_at'])
        tweet = {}
        print("saving")
        tweet['tweets'] = t['text']
        tweet['id'] = t['id']
        tweet['author'] = t['user']['screen_name']
        tweet['length'] = len(t['text'])
        tweet['DTG'] = tweettime
        tweet['source'] = self.clean_tweet(t['source'])[19:-2]
        tweet['likes'] = t['favorite_count']
        tweet['retweet_count'] = t['retweet_count']
        tweet['sentiment'] = self.analyze_sentiment(t)
        tweet['subject'] = self.subject
        df = pd.DataFrame(tweet, index=['tweets'])
        
        engine = sqlalchemy.create_engine('sqlite:///sent_data.db')
        df.to_sql("tweet_data", engine, if_exists="append", index=False)
        print("new tweet saved")

class TweetAnalyzer():
    """
    Gets sentiment from the tweets (and stores to database if called from outside)
    """
    
    def clean_tweet(self, tweet):
        try:
            return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())
        except:
            tweet = str(tweet)
            return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))
        if analysis.sentiment.polarity > 0:
            return 1 # positive tweet, happy days
        elif analysis.sentiment.polarity == 0:
            return 0 # dunno. meh.
        else:
            return -1 # must be a bit of a dick
    
    def tweets_to_df(self, tweets, subject):
        print("=======================")
        print(subject)
        print("++++++++++++")
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets'])
        df['id'] = np.array([t.id for t in tweets])
        df['author'] = np.array([t.author.name for t in tweets])
        df['length'] = np.array([len(t.text) for t in tweets])
        df['DTG'] = np.array([t.created_at for t in tweets])
        df['source'] = np.array([t.source for t in tweets])
        df['likes'] = np.array([t.favorite_count for t in tweets])
        df['retweet_count'] = np.array([t.retweet_count for t in tweets])
        df['sentiment'] = np.array([self.analyze_sentiment(t) for t in df['tweets']])
        df['subject'] = [subject for tweet in tweets]
        engine = sqlalchemy.create_engine('sqlite:///sent_data.db')
        df.to_sql("tweet_data", engine, if_exists="append", index=False)
        # self.analyze(df)
        return df
    
    def analyze(self, df):
        df['sentiment'] = np.array([TweetAnalyzer.analyze_sentiment(self.analyze_sentiment(t)) for t in df['tweets']])
    

if __name__ == '__main__':
    # manual testing only
    twitter_client = TwitterClient()
    api = twitter_client.get_twitter_client_api()
    
    tweets = api.user_timeline(screen_name="hillaryclinton", count=10)
    tweet_analyzer = TweetAnalyzer()
    
    # These are all the attributes of a tweet we can extract
    # print(dir(tweets[0]))
    # print(tweets[0].id)
    
    df = tweet_analyzer.tweets_to_df(tweets)
    df['sentiment'] = np.array([tweet_analyzer.analyze_sentiment(t) for t in df['tweets']])
    print(df.head)
