import csv
import json
import os
import streamlit as st
import tweepy
from pathlib import Path

from models import Tweet, Location


DATA_LOCAL_PATH = "data/tweets.json"
TWEETS_COUNT = 5000


@st.experimental_memo
def get_tweets_by_search(max_items: int) -> list[Tweet]:
    auth = tweepy.OAuthHandler(st.secrets.twitter.api_key, st.secrets.twitter.api_secret_key) 
    auth.set_access_token(st.secrets.twitter.access_token, st.secrets.twitter.access_token_secret_key)
    api = tweepy.API(auth)

    result = []
    for status in tweepy.Cursor(api.search_tweets, q="接触 (from:JRHbot)").items(max_items):
        result.append(Tweet(id=status.id, created_at=status.created_at.isoformat(), text=status.text))
    return result


@st.experimental_memo
def get_tweets_by_timeline(max_items: int) -> list[Tweet]:
    auth = tweepy.OAuthHandler(st.secrets.twitter.api_key, st.secrets.twitter.api_secret_key) 
    auth.set_access_token(st.secrets.twitter.access_token, st.secrets.twitter.access_token_secret_key)
    api = tweepy.API(auth)

    result = []
    for status in tweepy.Cursor(api.user_timeline, id="JRHbot").items(max_items):
        result.append(Tweet(id=status.id, created_at=status.created_at.isoformat(), text=status.text))
    return result


#@st.experimental_memo
def get_tweets_from_file(file_name: str) -> list[Tweet]:
    with open(file_name, "r", encoding="utf-8-sig") as f:
        obj = json.load(f)
        result: list[Tweet] = []
        for t in obj["tweets"]:
            result.append(Tweet(t["id"], t["created_at"], t["text"]))
        return result


def get_tweets() -> list[Tweet]:
    if os.path.exists(DATA_LOCAL_PATH):
        return get_tweets_from_file(DATA_LOCAL_PATH)
    
    tweets = get_tweets_by_timeline(TWEETS_COUNT)
    json_str = json.dumps({ "total": len(tweets), "tweets": [ t.__dict__ for t in tweets] }, ensure_ascii=False, indent=2)
    Path("data/tweets.json").write_text(json_str, encoding="utf-8-sig")
    return tweets


#@st.experimental_memo
def get_station_locations() -> dict[str, Location]:
    with open("data/station_locations.csv", "r", encoding="utf-8-sig", newline="") as file:
        csv_reader = csv.DictReader(file)
        result = {}
        for row in csv_reader:
            result[row["station"]] = Location(float(row["lat"]), float(row["lon"]))
        return result
