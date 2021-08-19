import numpy as np
import pandas as pd
from urllib import request
from tqdm import tqdm
import statsmodels.api as sm
import streamlit as st
import matplotlib.pyplot as plt
%matplotlib inline

#csvファイルからデータを入れる
df = pd.read_csv(' ')

#必要に応じてデータの型を確認・float型に変換

#時系列データの分解
res = sm.tsa.seasonal_decompose(df['　'],freq =12, model='multiplicative')### データの指定 ###
trend =res.trend  ### トレンドデータ ###
seasonal =res.seasonal  ### 季節データ ###
residual = res.resid ### 残差データ ###

#プロットして確認

### コレログラムの表示・自己相関係数の算出 ###
sm.graphics.tsa.plot_acf(df['　'],lags=40)

### ADF検定 ###定常性を満たすのかどうかの検定
result = sm.tsa.stattools.adfuller(df['icecream'])

### 学習用データの分割 ###
train_data =  df['　'][:int(len(df)*0.7)]### 8割のデータを学習に使う ###
test_data =  df['　'][int(len(df)*0.7):]### 2割のデータを検証に使う ###

#SARIMAモデル？
#予測モデルの作成





