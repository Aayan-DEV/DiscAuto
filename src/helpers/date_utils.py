import datetime 

def timestamp_as_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

'''
Citation:
("Python Tutorial: Build a SaaS App") -> Lines 3 - 4
'''
