import argparse
import requests
import pendulum


from github import Github

# 14 for test 12 real get up
GET_UP_ISSUE_NUMBER = 1   
GET_UP_MESSAGE_TEMPLATE = (
    "今天的起床时间是--{get_up_time}.\r\n\r\n 少玩手机，好好吃饭，多喝水，多运动，多发呆，多放松。\r\n\r\n "
)
BED_MESSAGE_TEMPLATE = ((
    "今天的睡觉时间是--{get_up_time}.\r\n\r\n 断网睡觉晚安好梦\r\n\r\n"
))
SENTENCE_API = "https://v1.jinrishici.com/all"
DEFAULT_SENTENCE = "赏花归去马如飞\r\n去马如飞酒力微\r\n酒力微醒时已暮\r\n醒时已暮赏花归\r\n"
TIMEZONE = "Asia/Shanghai"


def login(token):
    return Github(token)


def get_one_sentence():
    try:
        r = requests.get(SENTENCE_API)
        if r.ok:
            return r.json().get("content", DEFAULT_SENTENCE)
        return DEFAULT_SENTENCE
    except:
        print("get SENTENCE_API wrong")
        return DEFAULT_SENTENCE


def get_today_get_up_status(issue):
    comments = list(issue.get_comments())
    if not comments:
        return False
    latest_comment = comments[-2]
    latest_comment_night = comments[-1]
    now = pendulum.now(TIMEZONE)
    latest_day = pendulum.instance(latest_comment.created_at).in_timezone(
        "Asia/Shanghai"
    )
    latest_day_night = pendulum.instance(latest_comment_night.created_at).in_timezone(
        "Asia/Shanghai"
    )
    is_today = (latest_day.day == now.day) and (latest_day.month == now.month) and (latest_day_night.day == now.day) and (latest_day_night.month == now.month)
    return is_today


def make_get_up_message():
    sentence = get_one_sentence()
    now = pendulum.now(TIMEZONE)
    # 3 - 7 means early for me
    is_get_up_early = 5 <= now.hour <= 9    
    get_up_time = now.to_datetime_string()
    if 5 <= now.hour <= 18:
        body = GET_UP_MESSAGE_TEMPLATE.format(get_up_time=get_up_time)
    else:
        bedtime=get_up_time
        body = BED_MESSAGE_TEMPLATE.format(get_up_time=get_up_time)
    return body, is_get_up_early

def main(github_token, repo_name, weather_message, tele_token, tele_chat_id):
    u = login(github_token)
    repo = u.get_repo(repo_name)
    issue = repo.get_issue(GET_UP_ISSUE_NUMBER)
    is_toady = get_today_get_up_status(issue)
    # if is_toady:
    #     print("Today I have recorded the wake up time")
    #     return
    early_message, is_get_up_early = make_get_up_message()
    body = early_message
    if weather_message:
        weather_message = f"现在的天气是{weather_message}\n"
        body = weather_message + early_message
        issue.create_comment(body)
    # if is_get_up_early:
    #     issue.create_comment(body)
        # send to telegram
        if tele_token and tele_chat_id:
            requests.post(
                url="https://api.telegram.org/bot{0}/{1}".format(
                    tele_token, "sendMessage"
                ),
                data={
                    "chat_id": tele_chat_id,
                    "text": body,
                },
            )
    else:
        print("You wake up late")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")
    parser.add_argument(
        "--weather_message", help="weather_message", nargs="?", default="", const=""
    )
    parser.add_argument("--tele_token", help="tele_token", nargs="?", default="", const="")
    parser.add_argument("--tele_chat_id", help="tele_chat_id", nargs="?", default="", const="")
    options = parser.parse_args()
    main(
        options.github_token,
        options.repo_name,
        options.weather_message,
        options.tele_token,
        options.tele_chat_id,
    )
