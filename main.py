import streamlit as st
import tweepy


@st.experimental_memo
def get_tweets():
    auth = tweepy.OAuthHandler(st.secrets.twitter.api_key, st.secrets.twitter.api_secret_key) 
    auth.set_access_token(st.secrets.twitter.access_token, st.secrets.twitter.access_token_secret_key)
    api = tweepy.API(auth)

    for status in tweepy.Cursor(api.user_timeline, id="JRHbot").items(5):
        st.write(f"{status.created_at=}, {status.text=}")
        

st.title("鹿発生マップ")

get_tweets()