from datetime import datetime

def dt_to_str(dt):
    return str(dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

def tnow_iso():
    return datetime.now()

def tnow_iso_str():
    return dt_to_str(datetime.now())

def dt_from_str(dt_str):
    return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ')

def dt_from_ts(ts):
    return datetime.fromtimestamp(int(ts))
