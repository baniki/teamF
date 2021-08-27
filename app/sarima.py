import scrape3
import numpy as np
import pandas as pd
from urllib import request
from tqdm import tqdm
import statsmodels.api as sm
import streamlit as st
import matplotlib.pyplot as plt
import re

# -*- coding: utf-8 -*-
#csvファイルの指定
df = pd.read_csv('after_scrape_results.csv')

#データを整形
#価格を抽出
#税込の価格を取り出す。現在価格と即決価格があるときは現在価格を取り出す
current_price = [re.findall(r"\d+", i.replace(',', '')) for i in df['price']]
for j in range(len(current_price)):
  if current_price[j][1] == '0':
    current_price[j] = current_price[j][0]
  else:
    current_price[j] = current_price[j][1]
df["Price"] = pd.Series(current_price)

#時系列を抽出
time = [re.findall(r"\d+", i) for i in df['spec_table']]
year = []
month = []
date = []
hour = [] 
minute = []
for j in range(len(time)):
  year.append(int(time[j][6]))
  month.append(int(time[j][7]))
  date.append(int(time[j][8]))
  hour.append(int(time[j][9]))
  minute.append(int(time[j][10]))
df["year"] = pd.Series(year)
df["month"] = pd.Series(month)
df["date"] = pd.Series(date)
df["hour"] = pd.Series(hour)
df["minute"] = pd.Series(minute)

#要素を抽出
df = df.loc[:,['Price','month','date','hour']]

#float型に変換
df['Price'] = df['Price'].astype(float)

#外れ値の処理 #両側5%を除外
q = df.Price.quantile(0.975)
r = df.Price.quantile(0.025)
df = df.query('Price < @q')
df = df.query('Price > @r')

#データの順番を逆転・番号付け
df = df.iloc[::-1]
df.index = range(len(df))

#以下が時系列分析

#学習用データの分割
train_data =  df['Price'][:int(len(df)*0.8)]#8割のデータを検証に使う
test_data =  df['Price'][int(len(df)*0.8):]#2割のデータを検証に使う

# SARIMAパラメータ最適化（総当たりチェック）
# パラメータ範囲
# 季節成分以外のパラメータ範囲
min_p = 1; max_p = 2 # min_pは1以上を指定しないとエラー
min_d = 0; max_d = 1
min_q = 0; max_q = 3 

# 季節成分のパラメータ範囲
min_P = 0; max_P = 1
min_D = 0; max_D = 1
min_Q = 0; max_Q = 1

test_pattern = (max_p - min_p +1)*(max_d - min_d + 1)*(max_q - min_q + 1)*(max_P - min_P + 1)*(max_D - min_D + 1)*(max_Q - min_Q + 1)
s = 7 # 季節周期パラメータ
data = df['Price'] # 時系列データ

test_results = pd.DataFrame(index=range(test_pattern), columns=["model_parameters", "aic"])
num = 0
for p in tqdm(range(min_p, max_p + 1)):
    for d in range(min_d, max_d + 1):
        for q in range(min_q, max_q + 1):
            for P in range(min_P, max_P + 1):
                for D in range(min_D, max_D + 1):
                    for Q in range(min_Q, max_Q + 1):

                        sarima = sm.tsa.SARIMAX(
                                data, order=(p, d, q), 
                                seasonal_order=(P, D, Q, s), 
                                enforce_stationarity = False, 
                                enforce_invertibility = False
                            ).fit()
                        test_results.iloc[num]["model_parameters"] = "order=(" + str(p) + ","+ str(d) + ","+ str(q) + "), seasonal_order=("+ str(P) + ","+ str(D) + "," + str(Q) + ")"
                        test_results.iloc[num]["aic"] = sarima.aic
                        num += 1
                        
test_results=test_results[test_results.aic == min(test_results.aic)]
test_results=test_results.iloc[0,0]

result = re.findall(r"\d+", test_results)
result = [int(n) for n in result]
result.append(7)

order = tuple(result[:3])
seasonal_order = tuple(result[3:])

#SARIMAモデル（パラメータ最適化・総当たりaicベストを適用）
model = sm.tsa.SARIMAX(data,
                       order=order,
                       seasonal_order=seasonal_order,
                       enforce_stationality=False,
                       enforce_invertibility=False,
                       maxiter=1500
                       ).fit()

#学習させたモデルで、データを再現
sarima_pre = model.forecast(int(len(df)*0.2))

#ヒストグラムをstreamlitで表示
st.header('取引価格のヒストグラム')
fig, ax = plt.subplots()
ax.hist(df['Price'], bins=20)
plt.xlabel('price', fontsize=15)
plt.ylabel('frequency', fontsize=15)
st.pyplot(fig)

#streamlitでの表示
st.header('取引価格の時系列と予測')
fig = plt.figure()
ax = plt.axes()
#原系列の表示
plt.plot(df['Price'], label='original')

#2割の予測をを可視化
plt.plot(sarima_pre,label='prediction')
plt.axvline(x=len(data),c='r',linestyle='--')
plt.xlabel('time series',fontsize=15)
plt.ylabel('price', fontsize=15)
plt.legend()
st.pyplot(fig)






