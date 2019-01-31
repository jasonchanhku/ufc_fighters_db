import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import string
import re
import datetime
import sqlite3
import time
# created a list of links beforehand to iterate over

# list to store of page links
links = []
alphabets = sorted(set(string.ascii_lowercase))

# lists to store fighters info and stats
# Basic information
f_name = []
record = []
height = []
weight = []
reach = []
stance = []
dob = []
last_fought = []

# Career Statistics
slpm = []
stra = []
sapm = []
strd = []
td = []
tda = []
tdd = []
suba = []

def scrape_data():
    for alpha in alphabets:
        links.append("http://www.fightmetric.com/statistics/fighters?char=" + alpha + "&page=all")

        # now that we have a list of links we need to iterate it with BeautifulSoup
    for link in links:
        print(f"Currently on this link: {link}")

        data = requests.get(link)
        soup = BeautifulSoup(data.text, 'html.parser')
        names = soup.find_all('a', {'class': 'b-link b-link_style_black'}, href=True)   

        # list to store url page of fighters
        fighters = []

        for name in names:
            fighters.append(name['href'])

        fighters = sorted(set(fighters))

        for fighter in fighters:
            data = requests.get(fighter)
            soup = BeautifulSoup(data.text, 'html.parser')
            time.sleep(2)
            # fighter's name
            n = soup.find('span', {'class': 'b-content__title-highlight'})
            f_name.append(n.text.strip())
            print(f"Scraping the following fighter: {n.text.strip()}")

            # record
            rec = soup.find('span', {'class': 'b-content__title-record'})
            record.append(rec.text.strip().strip("Record: "))

            # bio box
            bio_box = soup.find('ul', {'class':'b-list__box-list'})
            bio_box = bio_box.find_all('li')

            # bio box - Height
            t = bio_box[0].text.strip().strip("Height:").strip()
            h = re.sub('[\"\']', '', t)
            height.append(h)

            # bio box - Weight
            w = bio_box[1].text.strip().strip("Weight:").strip().strip(" lbs.")
            try:
                weight.append(int(w))
            except:
                weight.append(w)

            # bio box - reach
            r = bio_box[2].text.strip().strip("Reach:").strip().strip("\"")
            try:
                reach.append(int(r))
            except:
                reach.append(r)

            # bio box - stance
            s = bio_box[3].text.strip().strip("STANCE:").strip()
            stance.append(s)

            # bio box - DOB
            date = bio_box[4].text.strip().strip("DOB:").strip()
            dob.append(date)

            # career statistics
            cs = soup.find('div', {'class': 'b-list__info-box-left clearfix'})
            cs = cs.find_all('li')

            # CS - SLPM
            slpm.append(float(cs[0].text.strip().strip("SLpM:").strip()))

            # CS - STRA
            stra.append(int(cs[1].text.strip().strip("Str. Acc.:").strip().strip("%"))/100)

            # CS - SAPM
            sapm.append(float(cs[2].text.strip().strip("SApM:").strip()))

            # CS - STRD
            strd.append(int(cs[3].text.strip().strip("Str. Def:").strip().strip("%"))/100)

            # CS - TD
            td.append(float(cs[5].text.strip().strip("TD Avg.:").strip()))

            # CS - TDA
            tda.append(int(cs[6].text.strip().strip("TD Acc.:").strip().strip("%").strip("%"))/100)

            # CS - TDD
            tdd.append(int(cs[7].text.strip().strip("TD Def.:").strip().strip("%"))/100)

            # CS - SUBA
            suba.append(float(cs[8].text.strip().strip("Sub Avg.:").strip()))

            # Last fought
            try:
                lf = soup.find('tr', {'class': 'b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click'})
                last_fought.append(lf.find_all('p', {'class': 'b-fight-details__table-text'})[12].text.strip())
            except:
                last_fought.append('--')

    return None

#preprocessing
# remove rows where DOB is null
# impute stance as orthodox for missing stances
def create_df():
    #create empty dataframe
    df = pd.DataFrame()
    
    #creating the df
    df["NAME"] = f_name
    df["DOB"] = dob
    df["RECORD"] = record
    df["LF"] = last_fought
    df["STANCE"] = stance
    df["Height"] = height
    df["Weight"] = weight
    df["REACH"] = reach
    df["SLPM"] = slpm
    df["SAPM"] = sapm
    df["STRA"] = stra
    df["STRD"] = strd
    df["TD"] = td
    df["TDA"] = tda
    df["TDD"] = tdd
    df["SUBA"] = suba
    
    
    return df

def weightclass(df):
    if df["Weight"] <= 115:
        return "strawweight"
    elif df["Weight"] <= 125:
        return "flyweight"
    elif df["Weight"] <= 135:
        return "bantamweight"
    elif df["Weight"] <= 145:
        return "featherweight"
    elif df["Weight"] <= 155:
        return "lightweight"
    elif df["Weight"] <= 170:
        return "welterweight"
    elif df["Weight"] <= 185:
        return "middleweight"
    elif df["Weight"] <= 205:
        return "lightheavyweight"
    else:
        return "heavyweight"

def age(df):
    year_now = int(datetime.datetime.now().strftime("%Y")) 
    year_born = int(df["DOB"].split(", ")[1])
    return (year_now - year_born)

def year_lf(df):
    year_now = int(datetime.datetime.now().strftime("%Y")) 
    year_last_fought = int(df["LF"].split(", ")[1])
    return (year_now - year_last_fought)
    
def preprocessing(df):
    # identifying NaNs
    df = df.replace('--',np.nan)
    df = df.replace('',np.nan)
    
    # removing useless rows
    df = df[df["DOB"].notnull()]
    df = df[df["Height"].notnull()]
    df = df[df["LF"].notnull()]
    
    # imputing missing values
    # Stance column - impute with Orthodox since most fighters are orthodox
    df["STANCE"] = df["STANCE"].fillna("Orthodox")
    
    # create weightclass column
    df["WeightClass"] = df.apply(weightclass, axis=1)
    
    # Reach column - impute with mean of respective weightclass
    df["REACH"] = df.groupby("WeightClass")['REACH'].apply(lambda x: x.fillna(round(x.mean(), 1)))
    
    # create age column
    df["Age"] = df.apply(age, axis=1)
    
    # create year since last fought
    df["Year_LF"] = df.apply(year_lf, axis=1)
    
    # created active or inactive flag
    df["Active"] = df["Year_LF"].apply(lambda x: True if x <= 4 else False)
    
    return df

scrape_data()
df = create_df()
df = preprocessing(df)
print("Scraping completed")

conn = sqlite3.connect('data.sqlite')
df.to_sql('data', conn, if_exists='replace')
print('Db successfully constructed and saved')
conn.close()