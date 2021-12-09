from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Dispatcher, ConversationHandler

from datetime import datetime
import os
import threading
try:
    import keys, main, brain
    # when using django (ie not testing)
except:
    from . import keys, main, brain
    
import pandas as pd
import numpy as np
import sqlalchemy


updater = None
dispatcher = None

updater = Updater(keys.BOT_TOKEN, use_context=True)

dispatcher = updater.dispatcher

users = []
robot_names = ["bot", "Bot", "robot", "Robot", "Wobot", "wobot"]


def start_bot():
    """
    Starts the telegram bot
    He lives on this machine but polls the API for messages
    """
    global updater
    global dispatcher
    
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('user', search_user))
    dispatcher.add_handler(CommandHandler('stream', search_keywords))
    dispatcher.add_handler(CommandHandler('getsentiment', get_sentiment))
    dispatcher.add_handler(MessageHandler(Filters.text, message_handler))
    
    updater.start_polling()
    updater.idle()
    
def start(update, context):
    global users
    users_name=update['message']['chat']['first_name']
    reply = "Hi " + users_name + ". I am Sentbot. I'll tell you what people think about stuff..."
    update.message.reply_text(reply)
    
    chat_id = update['message']['chat']['id']
    
def talk(update, context):
    """
    Respond to messages that don't contain commands but do contain the bot's name 
    (don't want it reacting to every message if its in a group chat)
    """
    
    users_name = update['message']['chat']['first_name']
    user_id = update['message']['chat']['id']    
    if any(word in update.message.text for word in robot_names):
        print("Message to robot!")
        messagetext = update.message.text
        message_namestripped = ''
        for word in messagetext.split():
            if word not in robot_names:
                message_namestripped = message_namestripped + word + ' '
        print(message_namestripped)
        update.message.reply_text(brain.chat(message_namestripped, users_name, user_id))
    else:
        print("From: " + users_name)
        print(update.message.text)



def message_handler(update, context):   
    """
    Telegram message handler - send to talk function
    If other key phrases are detected it can send with additional arguments or
    to other functions. This will be a future capability.
    """ 
    talk(update, context)
    
def search_user(update, context):
    """
    Use the twitter API to pull a specified number of tweets from a specified user to the DB
    """
    user = context.args[0]
    num = context.args[1]
    update.message.reply_text(f"Searching twitter for tweets by {user} ({num})")
    tweets = main.get_user_tweets(user, num)
    update.message.reply_text(f"Got {len(tweets)} from {user}")
    
def search_keywords(update, context):
    """
    Perform a keyword search on tweets for a desired duration
    """
    duration = context.args[0]
    words = context.args[1:]
    update.message.reply_text(f"Streaming tweets and filtering for:{context.args[1:]} for {context.args[0]} seconds")
    main.get_keyword_tweets([word for word in words], int(duration))
    update.message.reply_text("These will automatically save to the database and be included in any future analysis")

    
def get_sentiment(update, context):
    """
    Get a summary of the media sentiment of a particular topic
    This must be a topic we have stored in the DB
    """
    subject = context.args[0]
    engine = sqlalchemy.create_engine("sqlite:////home/main/Documents/Main/Code/Python/Data/web_displayer/sent_data.db") 
    news_df = pd.read_sql("news_data", engine)
    print(news_df.head())
    
    av_sent = np.mean(news_df['sentiment'])
    if av_sent < 0:
        overall = "negative"
    else:
        overall = "positive"
    print(np.mean(news_df['sentiment']))
    update.message.reply_text(f"The attitude in the media {overall}, with a sentiment score of {av_sent}")
        
    
    # debugging
    for item in news_df:
        print(item.subject)
    

    
    
bot_thread = threading.Thread(name='bot', target=start_bot)
# bot_thread.start() # handled by project root