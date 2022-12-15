import csv
import streamlit as st
import tweepy

from models import Tweet, Location


@st.experimental_memo
def get_tweets(max_items: int = 100) -> list[Tweet]:
    auth = tweepy.OAuthHandler(st.secrets.twitter.api_key, st.secrets.twitter.api_secret_key) 
    auth.set_access_token(st.secrets.twitter.access_token, st.secrets.twitter.access_token_secret_key)
    api = tweepy.API(auth)

    #for status in tweepy.Cursor(api.user_timeline, id="JRHbot").items(5):
    #    st.write(f"{status.created_at=}, {status.text=}")
    
    result = []
    for status in tweepy.Cursor(api.search_tweets, q="接触 (from:JRHbot)").items(max_items):
        #st.write(f"{status.created_at=}, {status.text=}")
        result.append(Tweet(id=status.id, created_at=status.created_at.isoformat(), text=status.text))
    return result


@st.experimental_memo
def get_tweets_2(max_items: int = 100) -> list[Tweet]:
    auth = tweepy.OAuthHandler(st.secrets.twitter.api_key, st.secrets.twitter.api_secret_key) 
    auth.set_access_token(st.secrets.twitter.access_token, st.secrets.twitter.access_token_secret_key)
    api = tweepy.API(auth)

    #for status in tweepy.Cursor(api.user_timeline, id="JRHbot").items(5):
    #    st.write(f"{status.created_at=}, {status.text=}")
    
    result = []
    for status in tweepy.Cursor(api.user_timeline, id="JRHbot").items(max_items):
        #st.write(f"{status.created_at=}, {status.text=}")
        result.append(Tweet(id=status.id, created_at=status.created_at.isoformat(), text=status.text))
    return result


#@st.experimental_memo
def get_station_locations() -> dict[str, Location]:
    with open("data/station_locations.csv", "r", encoding="utf-8-sig", newline="") as file:
        csv_reader = csv.DictReader(file)
        result = {}
        for row in csv_reader:
            result[row["station"]] = Location(float(row["lat"]), float(row["lon"]))
        return result
