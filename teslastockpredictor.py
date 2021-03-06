# -*- coding: utf-8 -*-
"""TeslaStockPredictor.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LuuRUi5nczLX7xyh9t3xArwT6ZTUD0gw
"""

import os 
import tensorflow as tf
import numpy as np 
import matplotlib.pyplot as plt
from matplotlib import style
import matplotlib
import pandas as pd
from datetime import datetime

from google.colab import drive
drive.mount('/content/gdrive', force_remount=True)
root_dir = "/content/gdrive/My Drive/"
data_dir=os.path.join(root_dir,"tsla.csv")

def plot_series(time, series, format="-", start=0, end=None):
    plt.plot(time[start:end], series[start:end], format)
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.grid(True)

df=pd.read_csv(data_dir)
df

df.drop(labels="Unnamed: 0", axis=1, inplace=True)
df.rename(columns={"Close*": "Close", "Adj Close**": "Adj Close"},inplace=True)
df

df=pd.DataFrame(df.values[::-1], df.index, df.columns)
df

adj_close=df['Adj Close']
adj_close.index = df['Date']

adj_close.head()

dates=df['Date']
dates1=[]
for date in dates:
    dates1.append(datetime.strptime(date, '%b %d, %Y'))
dates=pd.core.series.Series(dates1)

plt.figure(figsize=(13,8))
plt.style.use('fivethirtyeight')
plt.plot(dates1,adj_close)
plt.title("Tesla Adjusted Close Prices",loc='left')
plt.rcParams.update({'font.size': 14})

series = np.array(adj_close.values)
time = np.array(dates)

series=pd.to_numeric(series,errors='coerce',downcast='float')
series

series.dtype

split_time = 210
adj_train = series[:split_time]
adj_valid = series[split_time:]
dates_train=dates[:split_time]
dates_valid=dates[split_time:]

window_size = 16
batch_size = 32
shuffle_buffer_size = 50

adj_train=pd.to_numeric(adj_train,errors='coerce',downcast='float')
adj_train.astype(np.float)
adj_train

series[...,np.newaxis]

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[1:]))
    return ds.batch(batch_size).prefetch(1)

def model_forecast(model, series, window_size):
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size))
    ds = ds.batch(32).prefetch(1)
    forecast = model.predict(ds)
    return forecast

tf.keras.backend.clear_session()
tf.random.set_seed(51)
np.random.seed(51)
window_size = 64
batch_size = 256
train_set = windowed_dataset(adj_train, window_size, batch_size, shuffle_buffer_size)
print(train_set)
print(adj_train.shape)

model = tf.keras.models.Sequential([
  tf.keras.layers.Conv1D(filters=60, kernel_size=5,
                      strides=1, padding="causal",
                      activation="relu",
                      input_shape=[None, 1]),
  tf.keras.layers.LSTM(64, return_sequences=True),
  tf.keras.layers.LSTM(32, return_sequences=True),
  tf.keras.layers.Dense(24, activation="relu"),
  tf.keras.layers.Dense(12, activation="relu"),
  tf.keras.layers.Dense(1),
  tf.keras.layers.Lambda(lambda x: x * 400)
])

lr_schedule = tf.keras.callbacks.LearningRateScheduler(
    lambda epoch: 1e-8 * 10**(epoch / 20))
optimizer = tf.keras.optimizers.SGD(lr=1e-8, momentum=0.9)
model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])
history = model.fit(train_set, epochs=100, callbacks=[lr_schedule])

plt.semilogx(history.history["lr"], history.history["loss"])
#plt.axis([1e-8, 1e-3,135,250])

tf.keras.backend.clear_session()
tf.random.set_seed(51)
np.random.seed(51)
model = tf.keras.models.Sequential([
  tf.keras.layers.Conv1D(filters=60, kernel_size=5,
                      strides=1, padding="causal",
                      activation="relu",
                      input_shape=[None, 1]),
  tf.keras.layers.LSTM(256, return_sequences=True),
  tf.keras.layers.LSTM(128, return_sequences=True),
  tf.keras.layers.Dense(128, activation="relu"),
  tf.keras.layers.Dense(64, activation="relu"),
  tf.keras.layers.Dense(1),
  tf.keras.layers.Lambda(lambda x: x * 500)
])



optimizer = tf.keras.optimizers.SGD(lr=3e-7, momentum=0.9)
model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])
history = model.fit(train_set,epochs=350)

rnn_forecast = model_forecast(model, series[..., np.newaxis], window_size)
rnn_forecast = rnn_forecast[split_time - window_size:-1,-1, 0]

plt.figure(figsize=(20, 6))
plt.style.use('fivethirtyeight')
plt.title("Predictions vs Reality", loc="left")
plt.plot(dates_valid, adj_valid, label="Actual")
plt.plot(dates_valid, rnn_forecast, label= "Prediction")
plt.legend()

n = tf.keras.metrics.MeanAbsoluteError()
n.update_state(adj_valid, rnn_forecast)
print('Mean Absolute Error: ', n.result().numpy())
m = tf.keras.metrics.RootMeanSquaredError()
m.update_state(adj_valid, rnn_forecast)
print('Root Mean Squared Error: ', m.result().numpy())

