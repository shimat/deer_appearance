from typing import Iterable
import streamlit as st
import re
import json
from pathlib import Path
import pandas as pd
import numpy as np
import pydeck as pdk

from models import Tweet, Appearance, Location
from data_loader import get_tweets, get_station_locations


def extract_appearance(tweets: Iterable[Tweet]) -> Iterable[Appearance]:
    for tweet in tweets:
        for text in re.split("ならびに", tweet.text):
            #if not (match := re.search(r"(?P<datetime>\d{4}年\d{1,2}月\d{1,2}日\d{1,2}時\d{1,2}分)現在", tweet.text)):
            #    print(f"Error(datetime): {tweet.text=}")
            #    continue
            #datetime_string = match.group("datetime")
            text = re.sub("および|及び|、", " & ", text)
            sections: list[tuple[str, str]] = []
            for match in re.finditer(r"(?P<st1>\S+?駅?)(～|\-)(?P<st2>\S+?駅?)間", text):
                sections.append(
                    (match.group("st1").removesuffix("駅"), match.group("st2").removesuffix("駅")))
            if not sections:
                #print(f"Error(location): {tweet.text=}")
                continue
            
            if not (match := re.search(r"(?P<train>列車|特急\S+)が(?P<animal>\S+)と接触", text)):
                #print(f"Error(animal): {tweet.text=}")
                animal, train = "", ""
            else:
                animal, train = match.group("animal"), match.group("train")

            yield Appearance(tweet.created_at, sections, animal, train, text)


st.title("鹿発生マップ")

print("==========")

station_locations = get_station_locations()
#st.write(station_locations)

tweets = get_tweets()
#j = json.dumps({"tweets": [ t.__dict__ for t in tweets] }, ensure_ascii=False, indent=2)
#Path("tweets.json").write_text(j, encoding="utf-8-sig")

appearances = list(extract_appearance(tweets))
#st.write(appearances)
j = json.dumps([a.__dict__ for a in appearances], ensure_ascii=False, indent=2)
st.json(j)

locations = [
    Location.midpoint(station_locations[s[0]], station_locations[s[1]]) 
    for a in appearances 
    for s in a.sections]
st.write(locations)

data = pd.DataFrame(
   [l.to_tuple() for l in locations],
   columns=['lat', 'lon'])

icon_data = {
    # Icon from Wikimedia, used the Creative Commons Attribution-Share Alike 3.0
    # Unported, 2.5 Generic, 2.0 Generic and 1.0 Generic licenses
    "url": "https://upload.wikimedia.org/wikipedia/commons/c/c4/Projet_bi%C3%A8re_logo_v2.png",
    "width": 242,
    "height": 242,
    "anchorY": 242,
}
data["icon_data"] = None
for i in data.index:
    data["icon_data"][i] = icon_data

st.pydeck_chart(pdk.Deck(
    map_style="road",
    initial_view_state=pdk.ViewState(
        latitude=43.0,
        longitude=142.5,
        zoom=6,
        pitch=30,
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
    tooltip={"text": "{lat}"}
))