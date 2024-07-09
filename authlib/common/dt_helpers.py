import datetime as dt

# default ISO format
def dt_to_str(dt: dt.datetime, format='%Y-%m-%dT%H:%M:%S.%fZ') -> str:
    return str(dt.strftime(format))

# default ISO format
def dt_from_str(dt_str: str, format='%Y-%m-%dT%H:%M:%S.%fZ') -> dt.datetime:
    return dt.datetime.strptime(dt_str, format)

def dt_from_ts(ts: float) -> dt.datetime:
    return dt.datetime.fromtimestamp(int(ts))

def tnow_iso() -> dt.datetime:
    return dt.datetime.now()

def tnow_iso_str() -> str:
    return dt_to_str(dt.datetime.now())

