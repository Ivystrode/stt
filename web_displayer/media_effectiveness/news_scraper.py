import requests, sqlalchemy
from bs4 import BeautifulSoup
from textblob import TextBlob
from html.parser import HTMLParser
import pandas as pd
from tqdm import tqdm
import re
from dateutil.parser import parse, parserinfo

headers = {'User-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'}

class CustomParserInfo(parserinfo):
    """
    This is for saving dates as datetime objects
    """
    DAYS = list(range(1, 31))
    MONTHS = [("Jan", "January"), ("Feb", "February"), ("Mar", "March"), ("Apr", "April"), ("May", "May"), ("Jun", "June"), ("Jul", "July"), ("Aug", "August"), ("Sep", "September"), ("Oct", "October"), ("Nov", "November"), ("Dec", "December"),]
    YEARS = list(range(2020, 2050))

def clean(data):
    try:
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", data).split())
    except:
        data = str(data)
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", data).split())

def analyze_sentiment(data):
    analysis = TextBlob(clean(data))
    if analysis.sentiment.polarity > 0:
        return 1 # positive data, happy days
    elif analysis.sentiment.polarity == 0:
        return 0 # dunno. meh.
    else:
        return -1 # must be a bit of a dick
 

def scraper(subject):
    
    # store sites as a dictionary
    # key is site name, value is a list - element 1 is the search url, element 2 is the search result element, and 3 is the class
    sites = {"aljazeera": [f"https://www.aljazeera.com/search/{subject}", "a", "u-clickable-card__link"]}
    
    
    articles = {}
    df = pd.DataFrame()
    article_sites = []
    titles = []
    article_contents = []
    article_sentiments = []
    dates = []

    print("Scanning...\n")
    for site in tqdm(sites.items()):
        article_links = []
        print(site)
        
        r = requests.get(site[1][0], headers=headers)
        c = r.content
        soup = BeautifulSoup(c, "html.parser")
        page_results = soup.find_all(site[1][1], {"class": site[1][2]})
        for page in tqdm(page_results):
            print(page['href'])
            if str(page['href']) not in article_links:
                article_links.append(str(page['href']))
            i = 0
            for article in article_links:
                r = requests.get(article, headers=headers)
                c = r.content 
                soup = BeautifulSoup(c, "html.parser")
                page_title = soup.select_one(".article-header").getText()
                page_content = soup.select_one(".l-col").getText()
                sentiment = analyze_sentiment(page_title)
                # info = soup.find_all("div",  {"class": ".article-dates"})
                
                date_on_page = soup.find_all("div", {"class":"article-dates"})
                date = date_on_page[0].find_all("span")
                print(type(date))
                print(date)
                try:
                    print(date[i].getText())
                except:
                    i -= 1
                    print(date[i].getText())
                date = date[i].getText()
                if "Published On" in date:
                    date = date[12:]
                    print("removed published on")
                    print(date)
                print("=========")
                date = parse(date)
                dates.append(date)
                print(date)
                i += 1
                
                
                
                article_sites.append(site[0])
                titles.append(page_title)
                article_contents.append(page_content)
                article_sentiments.append(sentiment)
                # dates.append(date[1].getText())
                # print(dates)
    
    df['source'] = [site for site in article_sites]
    df['title'] = [title for title in titles]
    df['content'] = [content for content in article_contents]
    df['subject'] = subject
    df['sentiment'] = [sent for sent in article_sentiments]
    df['date'] = [date for date in dates]
    
    engine = sqlalchemy.create_engine('sqlite:///sent_data.db')
    df.to_sql("news_data", engine, if_exists="append", index=False)
    return df


if __name__ == '__main__':
    df = scraper("COP26")
    engine = sqlalchemy.create_engine('sqlite:///sent_data.db')
    df.to_sql("news_data", engine, if_exists="append", index=False)
