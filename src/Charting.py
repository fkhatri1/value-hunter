from API import API
from datetime import date, datetime, timedelta
from typing import List
import pandas as pd
import matplotlib.pyplot as plt
from utils import get_config, get_credentials
import logging

def chart(df, col='close', dt=None):
    if dt is not None:
        # find index of dt
        i = df.index.searchsorted(dt)
        df = df[i-10:i+11]
    else:
        df = df[-21:]

    x = df.index
    y = df[col]

    plt.plot(x,y,'go')
    plt.xticks(rotation="90")
    plt.show()

