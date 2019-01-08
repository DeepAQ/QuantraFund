from datetime import timedelta, datetime
import sys

from stock.data.stock_data import StockData
import stock.data.qtshare as qts


if __name__ == '__main__':
    a = int(sys.argv[1])
    b = int(sys.argv[2])
    sd = StockData()
    index = sd.get_index().index.values.tolist()
    print('Total:', len(index))
    end_date = datetime.now() - timedelta(days=1)
    count = 0
    for i in range(0, len(index)):
        if i >= a and i < b:
            code = index[i]
            try:
                info = sd.get_info(code=code, limit=1)
                if len(info) == 0:
                    max_date = datetime(2016, 12, 31)
                else:
                    max_date = info.iloc[0]['date']
                start_date = max_date + timedelta(days=1)
                df = qts.history(code, start_date, end_date)
                # df = df[df['volume'] != 0]
                df['adjclose'] = df['volume']
                print(df)
                df.to_sql('stock_data', sd.conn, index=False, if_exists='append')
                count += 1
                print('Finished:', code, ', progress:', i, '/', len(index))
            except:
                pass
