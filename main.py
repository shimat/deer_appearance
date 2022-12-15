from datetime import datetime
from typing import Iterable
import streamlit as st
import re
import json
from pathlib import Path
import pandas as pd
import numpy as np
import pydeck as pdk

from models import Tweet, Appearance, Location
from data_loader import get_tweets, get_tweets_2, get_station_locations


ICON_DATA = {
    "url": "https://raw.githubusercontent.com/shimat/deer_appearance/5554b83be16fc41d857d33ef83ee15d82b55f0e0/data/animal_deer.png",
    "width": 803,
    "height": 1053,
    "anchorY": 1053,
}
TWEETS_COUNT = 1000


def find_date_range(tweets: list[Tweet]):
    latest = datetime.fromisoformat(tweets[0].created_at)
    oldest = datetime.fromisoformat(tweets[-1].created_at)
    return (oldest.strftime("%Y/%m/%d"), latest.strftime("%Y/%m/%d"))


def extract_appearance(tweets: Iterable[Tweet]) -> Iterable[Appearance]:
    for tweet in tweets:
        for text in re.split("ならびに", tweet.text):
            #if not (match := re.search(r"(?P<datetime>\d{4}年\d{1,2}月\d{1,2}日\d{1,2}時\d{1,2}分)現在", tweet.text)):
            #    print(f"Error(datetime): {tweet.text=}")
            #    continue
            #datetime_string = match.group("datetime")
            text = re.sub("および|及び|、", " & ", text)
            text = re.sub("間と", "間 & ", text)
            sections: list[tuple[str, str]] = []
            for match in re.finditer(r"(?P<st1>\S+?)駅?(～|\-)(?P<st2>\S+?)[駅席]?間", text):
                sections.append(match.group("st1", "st2"))
            if not sections:
                #print(f"Error(location): {tweet.text=}")
                continue
            
            if not (match := re.search(r"(?P<train>列車|特急\S+)が(?P<animal>\S+)と接触", text)):
                #print(f"Error(animal): {tweet.text=}")
                #animal, train = "", ""
                continue
            else:
                animal, train = match.group("animal"), match.group("train")

            date_str = datetime.fromisoformat(tweet.created_at).strftime("%Y/%m/%d")
            yield Appearance(date_str, sections, animal, train, text)


st.title("鹿発生マップ")

station_locations = get_station_locations()

tweets = get_tweets_2(TWEETS_COUNT)

date_range = find_date_range(tweets)
#j = json.dumps({"tweets": [ t.__dict__ for t in tweets] }, ensure_ascii=False, indent=2)
#Path("tweets.json").write_text(j, encoding="utf-8-sig")

appearances = list(extract_appearance(tweets))
#j = json.dumps([a.__dict__ for a in appearances], ensure_ascii=False, indent=2)
#st.json(j)
st.text(f"集計期間: {date_range[0]}～{date_range[1]}, 件数: {len(appearances)}")

rows = []
for a in appearances:
    for s in a.sections:
        mid = Location.midpoint(station_locations[s[0]], station_locations[s[1]])
        train = "普通列車" if a.train == "列車" else a.train 
        text = f"{s[0]} ～ {s[1]} 駅間\n{a.datetime} {train}\n{a.animal}と衝突"
        rows.append((mid.lat, mid.lon, text, ICON_DATA))

data = pd.DataFrame(
   rows,
   columns=["lat", "lon", "text", "icon_data"])

st.pydeck_chart(pdk.Deck(
    map_style="light",
    initial_view_state=pdk.ViewState(
        latitude=43.6,
        longitude=142.7,
        zoom=6,
        pitch=0,
    ),
    layers=[
        pdk.Layer(
            "IconLayer",
            data=data,
            get_icon="icon_data",
            get_size=4,
            size_scale=15,
            get_position=["lon", "lat"],
            pickable=True,
        ),
    ],
    tooltip={"text": "{text}"}
))

#j = json.dumps([a.__dict__ for a in appearances], ensure_ascii=False, indent=2)
#st.json(j)

st.table(data)

st.markdown("""
---

利用データ:
+ JR北海道 在来線運行情報【非公式】[@JRHbot](https://twitter.com/JRHbot)
+ Twitter API: https://developer.twitter.com/
+ 鉄道駅LOD: https://uedayou.net/jrslod/
+ いらすとや: https://www.irasutoya.com/2013/07/blog-post_4288.html
""")

