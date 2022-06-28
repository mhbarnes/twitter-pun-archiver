"""
File: utils.py
Description: Python file containing functions for Twitter pun archiver script.
"""

# For Google Drive/Doc API
from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import tweepy       # For Twitter API access

import dotenv                   # For loading .env
import os                       # For file management
import re                       # For parsing tweet format
from datetime import datetime   # For storing last run time

# Load environment variables
base_dir = os.path.abspath(os.path.dirname(__file__))
dotenv_file = os.path.join(base_dir, '.env')
dotenv.load_dotenv(dotenv_file)

TWT_API_KEY = os.getenv("TWT_API_KEY")
TWT_API_KEY_SECRET = os.getenv("TWT_API_KEY_SECRET")
TWT_ACCESS_TOKEN = os.getenv("TWT_ACCESS_TOKEN")
TWT_ACCESS_TOKEN_SECRET = os.getenv("TWT_ACCESS_TOKEN_SECRET")
TWT_BEARER_TOKEN = os.getenv("TWT_BEARER_TOKEN")
TWT_ACCOUNT_NAME = os.getenv("TWT_ACCOUNT_NAME")
TWT_ACCOUNT_ID = int(os.getenv("TWT_ACCOUNT_ID"))
LAST_SEEN_TWEET_ID = os.getenv("LAST_SEEN_TWEET_ID")
LAST_RUN_DATE = os.getenv("LAST_RUN_DATE")
DOCUMENT_ID = os.getenv("DOCUMENT_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Globals
ITALICS_OFFSET = 9
last_seen_tweet_id_found = True
pun_format_regex = re.compile(r"(.+)\n\n(.+$)")


#######################################
# Functions
########################################
def archive_tweets(gd_service, user_tweets: dict):
    """
    Core archiver function. UP
    """
    # Update the year header in the Google Doc, if needed.
    doc_update_year(gd_service)

    for tweet in reversed(user_tweets["data"]):
        # Check if tweet is a pun tweet.
        result = pun_format_regex.match(tweet["text"])
        if (result == None):
            continue

        # Parse and log pun tweet
        created_at = datetime.strptime(tweet["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        date = created_at.strftime("%m/%d/%Y")
        tweet_setup = result.group(1)
        tweet_punchline = result.group(2)
        log_tweet_info(tweet, date, tweet["id"], tweet_setup, tweet_punchline)
        formatted_tweet = format_tweet(date, tweet_setup, tweet_punchline)

        # Format and export to Google Doc
        doc_add_text(formatted_tweet, 6, gd_service)
        doc_format_text(6, len(date + tweet_setup + tweet_punchline) + ITALICS_OFFSET, gd_service)
        doc_italicize_punchline(len(date + tweet_setup) + ITALICS_OFFSET,
            len(date + tweet_setup + tweet_punchline) + ITALICS_OFFSET,
            gd_service)
        print("Tweet exported to doc.")
        save_last_seen_id(tweet["id"])


def twt_auth_passed():
    """
    Authenticates Twitter API Key and Access Token.

    Returns:
        Tweepy client object
    """
    client = tweepy.Client(return_type = dict,
        bearer_token = TWT_BEARER_TOKEN,
        consumer_key = TWT_API_KEY,
        consumer_secret = TWT_API_KEY_SECRET,
        access_token = TWT_ACCESS_TOKEN,
        access_token_secret = TWT_ACCESS_TOKEN_SECRET)
    return client


# Dotenv get/set Functions
def save_last_seen_id(new_id: str):
    """
    Save last seen tweet ID in .env.

    Returns:
        None
    """
    os.environ["LAST_SEEN_TWEET_ID"] = new_id.strip("\"'")
    dotenv.set_key(dotenv_file, "LAST_SEEN_TWEET_ID", 
        os.environ["LAST_SEEN_TWEET_ID"].strip("\"'"))
    print(f"Saved last seen tweet ID: {new_id}")


def save_last_run_date(date: str):
    """
    Save last script run date .env.

    Returns:
    None
    """
    os.environ["LAST_RUN_DATE"] = date.strip("\"'")
    dotenv.set_key(dotenv_file, "LAST_RUN_DATE", 
        os.environ["LAST_RUN_DATE"].strip("\"'"))
    print(f"Saved last run date: {date}")


# Twitter Functions
def get_tweets(client: tweepy.Client, last_seen_tweet_id: str, 
    num_tweet_retrieve: int = 100
):
    """
    Retrieves the latest tweets from the account in .env.

    Returns:
        List of Statuses (tweets) if successful.
    """
    if (last_seen_tweet_id_found):
        user_tweets = client.get_users_tweets(id = TWT_ACCOUNT_ID,
            exclude = ["replies", "retweets"],
            max_results = num_tweet_retrieve,
            since_id = last_seen_tweet_id,
            tweet_fields = ["id", "text", "created_at"])
        return user_tweets
    else:
        return -1


def log_tweet_info(tweet: dict, date: str, id: str, setup: str, punchline: str):
    """
    Prints information about tweet to console.

    Returns:
        None.
    """
    print(f"New tweet ID: {id}")
    print(f"  date: {date}")
    print(f"  setup: {setup}")
    print(f"  punchline: {punchline}")


def format_tweet(date: str, setup: str, punchline: str):
    """
    Returns tweet text formatted for the Google Doc.
    """
    return f"{date}\n{setup}\n\t{punchline}\n\n"

# Google Doc Functions
def doc_add_text(tweet_text: str, idx: int, service):
    """
    Sends a request to update the Google Doc with new pun.
    """
    requests = [
                {
                'insertText': {
                    'location': {
                        'index': idx,
                    },
                    'text':	 tweet_text
                }
            }
        ]
    service.documents().batchUpdate(
        documentId=DOCUMENT_ID, body={'requests': requests}).execute()


def doc_format_text(start_idx: int, end_idx: int, service, 
    font_style: str = 'Arial', font_size: int = 11
):
    """
    Sends a request to set Google Doc text to "Normal Text" setting.
    """
    requests = [
        {
            'updateParagraphStyle': {
                'range': {
                    'startIndex': start_idx,
                    'endIndex':  end_idx
                },
                'paragraphStyle': {
                    'namedStyleType': 'NORMAL_TEXT',
                    'spaceAbove': {
                        'magnitude': 0,
                        'unit': 'PT'
                    },
                    'spaceBelow': {
                        'magnitude': 0,
                        'unit': 'PT'
                    }
                },
                'fields': 'namedStyleType,spaceAbove,spaceBelow'
            }
        }
    ]
    service.documents().batchUpdate(
        documentId=DOCUMENT_ID, body={'requests': requests}).execute()


def doc_italicize_punchline(start_idx: int, end_idx: int, service):
    """
    Sends a request to italicize the punchline in the Google Doc.
    """
    requests = [
        {
            'updateTextStyle': {
                'range': {
                    'startIndex': start_idx,
                    'endIndex': end_idx
                },
                'textStyle': {
                    'italic': True
                },
                'fields': 'italic'
            }
        }
    ]
    service.documents().batchUpdate(
        documentId=DOCUMENT_ID, body={'requests': requests}).execute()


def doc_update_year(service):
    """
    Updates the year header in the Google Doc if last run was in previous year.
    """
    last_run = datetime.strptime(LAST_RUN_DATE, "%m/%d/%Y")
    now = datetime.now()
    if (last_run.year < now.year):
        year_str = str(now.year) + '\n'
        doc_add_text(year_str, 1, service)