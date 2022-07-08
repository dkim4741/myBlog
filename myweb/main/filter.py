from main import app, datetime, time


@app.template_filter("formatdatetime")
def format_datetime(value):
    if value is None:
        return ""

    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp)-datetime.utcfromtimestamp(now_timestamp)
    # Time Difference = datetime current time - datetime UTC time
    value = datetime.fromtimestamp((int(value) / 1000)) + offset 
    # sec형태로 db에 저장된글 작성시간을 다시 millisec으로 변경,                       
    # db에 저장된 UTC 시간 + 시간차 = 현재로컬시간 기준으로 작성일자가 표기됨
    return value.strftime('%Y-%m-%d %H:%M:%S')