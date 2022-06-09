import logging
import requests
import json
import yaml


logging.basicConfig(filename="./noticias_parachains.log",
                    filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%m/%d %H:%M:%S")

logger = logging.getLogger("noticiasparachain")
logger.setLevel(logging.INFO)


def read_config():
    config_file = yaml.safe_load(open("config.yml"))
    return config_file


config_info = read_config()
bearer_token = config_info["tw_config"]["bearer_token"]


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r


def get_follower_count(set, user):
    min_followers = 5e3
    query = f"https://api.twitter.com/2/users/by?usernames={user}&user.fields=public_metrics"
    response = requests.get(
        query,
        auth=bearer_oauth, stream=True,
    )
    if response.status_code != 200:
        ex = f'43 Cannot get stream (HTTP {response.status_code}): {response.text}'
        raise Exception(ex)
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)
            big_accounts = [user["username"] for user in json_response["data"] if
                            user["public_metrics"]["followers_count"] > min_followers]
            return big_accounts


def format_stream_query(tw_handles):
    handles_query_complete = []
    for chunk in tw_handles:
        handles_query = " OR ".join([f'from: {tw}' for tw in chunk])
        handles_query = "(" + handles_query + ") -is:retweet"
        handles_query_complete.append(handles_query)
    sample_rules = []
    for query in handles_query_complete:
        single_rule = {"value": query}
        sample_rules.append(single_rule)
    if len(sample_rules) > 5:
        ex = f'65 Too many rules: {len(sample_rules)}/5'
        raise Exception(ex)
    logger.info(f'> Using {len(sample_rules)}/5 rules')
    rule_nchar = []
    for rule in sample_rules:
        rule_nchar.append([len(rule["value"])])
    logger.info(f'> Max length: {max(rule_nchar)}/512')
    return sample_rules


def get_big_accounts(usernames):
    big_ones = []
    max_users_query = 100
    if len(usernames) > max_users_query:
        chunk = len(usernames) // max_users_query  # floor
        for i in range(chunk):
            i = i * max_users_query
            some_usernames = usernames[i:i + max_users_query]
            big_ones_from_some = get_follower_count(set, user=",".join(some_usernames))
            big_ones = big_ones + big_ones_from_some
    else:
        big_ones = get_follower_count(set, user=",".join(usernames))
    logger.info(f'> Trimming from {len(usernames)} to {len(big_ones)} biggest accounts')
    return big_ones


def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        ex = f'64 Cannot get rules (HTTP {response.status_code}): {response.text}'
        raise Exception(ex)
    return response.json()


def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        ex = f'115 Cannot delete rules (HTTP {response.status_code}): {response.text}'
        raise Exception(ex)


def set_rules(delete, rules):
    payload = {"add": rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        ex = f'128 Cannot add rules (HTTP {response.status_code}): {response.text}'
        raise Exception(ex)


def get_stream(set):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream?expansions=author_id,in_reply_to_user_id&tweet.fields=reply_settings",
        auth=bearer_oauth, stream=True,
    )
    if response.status_code != 200:
        ex = f'139 Cannot get stream (HTTP {response.status_code}): {response.text}'
        raise Exception(ex)
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)
            username = json_response["includes"]["users"][0]["username"]
            if "in_reply_to_user_id" in json_response["data"] and (
                    json_response["data"]["in_reply_to_user_id"] != json_response["data"]["author_id"]):
                logger.info(f"{username}: Response to other user")
                continue
            if json_response["data"]["reply_settings"] != "everyone":
                logger.info(f"{username}: Not for everyone!")
                continue
            if "retweeted_status" in json_response["data"]:
                logger.info(f"{username}: Retweet")
                continue
            msg = format_tw_url(json_response)
            send_tg(config_info, msg)


def send_tg(config, msg, to_dev=False):
    bot_token = config["tg_config"]["bot_token"]
    chat_id = config["tg_config"]["dev_chat_id"] if to_dev else config["tg_config"]["chat_id"]
    url_msg = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    params = {'chat_id': chat_id,
              "text": msg,
              'disable_web_page_preview': False,
              'parse_mode': "Markdown"}
    response = requests.post(url_msg, params=params)
    if response.status_code != 200:
        ex = f'170 Cannot send message (HTTP {response.status_code}): {response.text}'
        raise Exception(ex)


def format_tw_url(tw_json):
    username = tw_json["includes"]["users"][0]["username"]
    author_id = tw_json["data"]["author_id"]
    if "in_reply_to_user_id" in tw_json["data"] and (tw_json["data"]["in_reply_to_user_id"] == author_id):
        thread = "\U0001F9F5"
    else:
        thread = ""
    # I had to escape "_" from the text but not from the URL (username)
    tw_text = tw_json["data"]["text"]
    tw_text = tw_text.replace("_", r"\_")
    tw_id = tw_json["data"]["id"]
    url = f'https://twitter.com/{username}/status/{tw_id}'
    name = tw_json["includes"]["users"][0]["name"]
    name = name.replace("_", r"\_")
    msg_header = f'[\U0001F426]({url}){thread} #{name}:'
    url_md = f'[Permalink](https://twitter.com/{username}/status/{tw_id})'
    full_msg = f'{msg_header}\n{tw_text}\n\n{url_md}'
    # full_msg = full_msg.replace("_", r"%5F")
    logger.info(name)
    # ToDo
    # Handle the cursive when there's some "_" in the message
    # Check if there are more special characters to escape
    return full_msg


def chop_query(usernames):
    chopped_accounts = []
    names_by_rule = 20
    chunk = len(usernames) // names_by_rule
    for i in range(chunk):
        i = i * 10
        chunked = usernames[i:i + names_by_rule]
        chopped_accounts.append(chunked)
    last_chunk = usernames[chunk * names_by_rule:]
    chopped_accounts.append(last_chunk)
    return chopped_accounts


def main():
    try:
        logger.info(f'> Starting')
        usernames = config_info["tw_config"]["handles"]
        big_accounts = get_big_accounts(usernames)
        chopped_big_accounts = chop_query(big_accounts)
        handles_query = format_stream_query(chopped_big_accounts)
        rules = get_rules()
        delete = delete_all_rules(rules)
        set = set_rules(delete, handles_query)
        get_stream(set)
    except Exception as ex:
        logger.error(f'>(222) {ex}')
        send_tg(config_info, msg=ex, to_dev=True)
        exit(1)


if __name__ == "__main__":
    main()

# ToDo
# Create log and dump there the Exceptions?
