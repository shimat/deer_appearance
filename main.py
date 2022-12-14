from datetime import datetime
from typing import NamedTuple, Iterable
import streamlit as st
import tweepy
import re


class Tweet(NamedTuple):
    created_at: datetime
    text: str


class Appearance(NamedTuple):
    datetime: datetime
    station_1: str
    station_2: str
    animal: str
    train: str



@st.experimental_memo
def get_tweets() -> list[Tweet]:
    auth = tweepy.OAuthHandler(st.secrets.twitter.api_key, st.secrets.twitter.api_secret_key) 
    auth.set_access_token(st.secrets.twitter.access_token, st.secrets.twitter.access_token_secret_key)
    api = tweepy.API(auth)

    #for status in tweepy.Cursor(api.user_timeline, id="JRHbot").items(5):
    #    st.write(f"{status.created_at=}, {status.text=}")
    
    result = []
    for status in tweepy.Cursor(api.search_tweets, q="接触 (from:JRHbot)").items(100):
        #st.write(f"{status.created_at=}, {status.text=}")
        result.append(Tweet(status.created_at, status.text))
    return result


def extract_appearance(tweets: Iterable[Tweet]) -> Iterable[Appearance]:
    for tweet in tweets:        
        #if not (match := re.search(r"(?P<datetime>\d{4}年\d{1,2}月\d{1,2}日\d{1,2}時\d{1,2}分)現在", tweet.text)):
        #    print(f"Error(datetime): {tweet.text=}")
        #    continue
        #datetime_string = match.group("datetime")

        if not (match := re.search(r"(?P<loc1>\S+駅?)(～|\-)(?P<loc2>\S+駅?)間", tweet.text)):
            print(f"Error(location): {tweet.text=}")
            continue
        loc1, loc2 = match.group("loc1"), match.group("loc2")
        
        if "および" in tweet.text or \
            "ならびに" in tweet.text or \
            not (match := re.search(r"(?P<train>列車|特急\S+)が(?P<animal>\S+)と接触", tweet.text)):
            print(f"Error(animal): {tweet.text=}")
            animal = tweet.text
            train = ""
        else:
            animal, train = match.group("animal"), match.group("train")

        yield Appearance(tweet.created_at, loc1, loc2, animal, train)
        #print(match.group("datetime"))

    return []

st.title("鹿発生マップ")

print("==========")
tweets = get_tweets()
st.write(tweets)
appearances = extract_appearance(tweets)
st.write(list(appearances))