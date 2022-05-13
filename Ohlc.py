import json
import pprint as pp
from datetime import datetime


def to_timestamp(dateString):
    element = datetime.strptime(dateString, '%d/%m/%Y')
    return int(datetime.timestamp(element))

def to_date(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%d/%m/%Y')


class Ohlc():
    def __init__(self, tuple):
        (self.close_ts,
         self.open,
         self.high,
         self.low,
         self.close,
         self.volume,
         self.quote_volume) = tuple
        self.close_dt = to_date(self.close_ts)

    def __repr__(self):
        return pp.pformat({
            'close_dt': self.close_ts,
            'price': {
              'open': self.open,
              'high': self.high,
              'low': self.low,
              'close': self.close,
            },
        })