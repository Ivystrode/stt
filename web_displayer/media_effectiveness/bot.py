from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Dispatcher, ConversationHandler

from datetime import datetime
import os
import threading
try:
    import keys, main, brain
    # when using django
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
robot_names = ["MaxiBot", "Maxibot", "maxibot", "Maxi", "maxi", "bot", "Bot", "robot", "Robot", "Wobot", "wobot"]


def start_bot():
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
    # bot_db.add_authorised_user(int(chat_id), users_name, "regular")
    
def talk(update, context):
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
    if any(word in update.message.text for word in robot_names) and ("what" in update.message.text or "tell" in update.message.text or "show" in update.message.text or "What" in update.message.text or "Tell" in update.message.text or "Show" in update.message.text) and ("news" in update.message.text or "headlines" in update.message.text or "going on in the world" in update.message.text): 
        get_headlines(update, context)
    elif ("what" in update.message.text or "which" in update.message.text or "What" in update.message.text or "Which" in update.message.text) and ("server" in update.message.text):
        server(update, context)
    else:
        talk(update, context)
    
def search_user(update, context):
    user = context.args[0]
    num = context.args[1]
    update.message.reply_text(f"Searching twitter for tweets by {user} ({num})")
    tweets = main.get_user_tweets(user, num)
    update.message.reply_text(f"Got {len(tweets)} from {user}")
    
def search_keywords(update, context):
    duration = context.args[0]
    words = context.args[1:]
    update.message.reply_text(f"Streaming tweets and filtering for:{context.args[1:]} for {context.args[0]} seconds")
    main.get_keyword_tweets([word for word in words], int(duration))
    update.message.reply_text("These will automatically save to the database and be included in any future analysis")

    
def get_sentiment(update, context):
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
        
    
    
    for item in news_df:
        print(item.subject)
    

    
    
bot_thread = threading.Thread(name='bot', target=start_bot)
# bot_thread.start()