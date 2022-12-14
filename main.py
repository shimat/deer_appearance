from datetime import datetime, timedelta, date
import json
import logging 
from pathlib import Path
import re
from typing import Iterable, Any
import pandas as pd
import numpy as np
import pydeck as pdk
import streamlit as st

from models import Tweet, Appearance, Location
from data_loader import get_tweets, get_station_locations


#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
#fh = logging.FileHandler("error_log.txt", mode="w", encoding="utf-8-sig")
#ch = logging.StreamHandler()
#logger.addHandler(fh)
#logger.addHandler(ch)

ICON_DATA = {
    "鹿": {
        "url": "https://raw.githubusercontent.com/shimat/deer_appearance/ec75280793daa24d76b2ed591ca1125bfd1877a6/image/animal_deer.png",
        "width": 305,
        "height": 400,
        "anchorY": 400,
    },
    "熊": {
        "url": "https://raw.githubusercontent.com/shimat/deer_appearance/6e083a7bcfb20e9fdc66efc35b1c4131d07b4ec7/image/animal_bear_character.png",
        "width": 400,
        "height": 400,
        "anchorY": 400,
    },
    "_その他_": {
        "url": "https://raw.githubusercontent.com/shimat/deer_appearance/6e083a7bcfb20e9fdc66efc35b1c4131d07b4ec7/image/mark_question.png",
        "width": 157,
        "height": 200,
        "anchorY": 200,
    },
}


def get_icon_data(object: str) -> dict[str, Any]:
    return ICON_DATA.get(object, ICON_DATA["_その他_"])


def find_date_range(tweets: list[Tweet]) -> tuple[datetime, datetime]:
    latest = datetime.fromisoformat(tweets[0].created_at)
    oldest = datetime.fromisoformat(tweets[-1].created_at)
    return (oldest, latest)


def generate_date_sequence(start_date: datetime, end_date: datetime) -> Iterable[str]:
    for n in range(int((end_date - start_date).days) + 1):
        yield (start_date + timedelta(n)).strftime("%Y-%m-%d")


def get_elapsed_days(start_date: str, end_date: str) -> int:
    sd = datetime.strptime(start_date, "%Y-%m-%d")
    ed = datetime.strptime(end_date, "%Y-%m-%d")
    return (ed - sd).days


def extract_appearance(tweets: Iterable[Tweet]) -> Iterable[Appearance]:    
    for tweet in tweets:
        for text in re.split("ならびに", tweet.text):

            #text = text.replace("\u3000", "")
            text = re.sub("および|及び|、", " & ", text)
            text = re.sub("間と", "間 & ", text)

            if match := re.search(r"(?P<train>貨物列車|列車|特急\S+|快速\S*?|はこだてライナー)(が|は.+?(で|において))(?P<reason>(?P<object>\S+)(と|を|の)(接触|衝突|衝撃|発見|巻き込んで))", text):
                reason, object, train = match.group("reason", "object", "train")
            else:
                #logger.debug(f"Error(animal): {tweet.text=}")
                #f.write(f"Error(animal): {text=}\n")
                continue
            train = "普通列車" if train == "列車" else train 

            sections: list[tuple[str, str]] = []
            for match in re.finditer(r"(?P<st1>\S+?)駅?(～|\~|\-|－|(?<!ビ)ー(?!ル))(?P<st2>\S+?)[駅席]?(間で|間にて|間?(付近)?において|間の.+?踏切)", text):
                sections.append(match.group("st1", "st2"))
            if not sections:
                for match in re.finditer(r"(?P<st>\S+?)(駅構内|駅?付近において)", text):
                    sections.append((match.group("st"), ""))
            if not sections:
                #logger.debug(f"Error(location): {tweet.text=}")
                #f.write(f"Error(location): {text=}\n")
                continue            

            date_str = datetime.fromisoformat(tweet.created_at).strftime("%Y-%m-%d")
            yield Appearance(date_str, sections, reason, object, train, text)


st.set_page_config(page_title="JR北海道 鹿衝突マップ")
st.title("JR北海道 鹿衝突マップ")

station_locations = get_station_locations()

tweets = get_tweets()
#j = json.dumps({ "total": len(tweets), "tweets": [ t.__dict__ for t in tweets] }, ensure_ascii=False, indent=2)
#Path("data/tweets.json").write_text(j, encoding="utf-8-sig")

appearances = list(extract_appearance(tweets))
#j = json.dumps([a.__dict__ for a in appearances], ensure_ascii=False, indent=2)
#st.json(j)

rows = []
for a in appearances:
    for s in a.sections:
        if s[1] == "":
            lat, lon = station_locations[s[0]].to_tuple()
            place = f"{s[0]}駅"
        else:
            lat, lon = Location.midpoint(station_locations[s[0]], station_locations[s[1]]).to_tuple()
            place = f"{s[0]} ～ {s[1]} 駅間"
        text = f"{place}\n{a.date} {a.train}\n{a.reason}"
        rows.append((lat, lon, text, a.date, get_icon_data(a.object)))

data = pd.DataFrame(
   rows,
   columns=["lat", "lon", "text", "date", "icon_data"])

oldest, latest = find_date_range(tweets)
date_sequence = list(generate_date_sequence(oldest, latest))

oldest_, latest_ = st.select_slider(
    "期間を選択",
    options=date_sequence,
    value=(date_sequence[0], date_sequence[-1]))

data = data.query(f"'{oldest_}' <= date <= '{latest_}'")
st.text(f"集計期間: {oldest_} ～ {latest_} ({get_elapsed_days(oldest_, latest_)}日)\n件数: {len(data)}")

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

#st.table(data)

st.markdown("""
---

利用データ:
+ JR北海道 在来線運行情報【非公式】[@JRHbot](https://twitter.com/JRHbot)
+ Twitter API: https://developer.twitter.com/
+ 鉄道駅LOD: https://uedayou.net/jrslod/
+ いらすとや: https://www.irasutoya.com/
""")

