from django.shortcuts import render
from.forms import SentimentDisplayForm, GetNewNews

import plotly.graph_objs as go
from plotly.offline import plot

from utilities import news_scraper

import sqlalchemy
import pandas as pd

# Create your views here.
def sentiment_displayer(request):
    """
    Search news websites for new topics and show sentiment about other topics
    Including scatter plot of various news orgs on a topic
    And line plot of sentiment over time (for single news org)
    """
    
    sentiment_display_form = SentimentDisplayForm()
    get_new_news_form = GetNewNews()
    
    context = {"sentiment_display_form": sentiment_display_form,
               "get_new_news_form": get_new_news_form}
    
    # engine = sqlalchemy.create_engine("sqlite:////home/main/Documents/Main/Code/Python/Data/web_displayer/sent_data.db") 
    # df = pd.read_sql("news_data", engine)

    
    if request.method == "POST" and "getnewnews" in request.POST:
        form = GetNewNews(request.POST)
        print("GETTING NEW NEWS")
        if form.is_valid():
            subject = form.cleaned_data['subject']
            print(subject)
            news_scraper.scraper(subject)
            # engine = sqlalchemy.create_engine("sqlite:////home/main/Documents/Main/Code/Python/Data/web_displayer/sent_data.db") 
            # df = pd.read_sql("news_data", engine)
            return render(request, "sentiment_display/sentiment_display.html", context)
        
    elif request.method == "POST" and "getsentiment" in request.POST:
        form = SentimentDisplayForm(request.POST)
        print("GETTING SENTIMENT")
        if form.is_valid():
            subject = form.cleaned_data['subject']
            print(subject)
            
            # get topic data
            engine2 = sqlalchemy.create_engine("sqlite:////home/main/Documents/Main/Code/Python/Data/web_displayer/sent_data.db") 
            news_df = pd.read_sql("news_data", engine2)
            news_topics = news_df.loc[news_df['subject'] == subject]
            print("TWEET DF:")
            print(news_topics.head())
            
            # create the chart
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=news_topics['date'], y=news_topics['sentiment'], mode="markers",name=subject))
            fig2.update_layout(title="Tweet likes", xaxis_title="Date", yaxis_title="Sentiment")
            fig2.update_layout(template='plotly_dark', title=f"{subject} news sentiment report over time")
            
            # put chart on the page
            chart_div = plot(fig2, output_type='div')
            context['sentchart'] = chart_div
            return render(request, "sentiment_display/sentiment_display.html", context)
            
    return render(request, "sentiment_display/sentiment_display.html", context)