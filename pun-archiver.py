#!/usr/bin/python

"""
File: pun-archiver.py
Description: Python script which archives and formats puns tweeted out from a 
    designated account to a Google Doc.
"""

########################################
# Files
########################################
import utils as pa

#######################################
# Main
########################################
def main():
    # Authenticate to Twitter
    client = pa.twt_auth_passed()
    if (client == None):
        return 1
    
    # Get last seen tweet ID
    last_seen_id = pa.LAST_SEEN_TWEET_ID
    print(f"Last seen tweet ID: {last_seen_id}")

    # Gets latest tweets posted by user
    user_tweets = pa.get_tweets(client, last_seen_id)
    if ("meta" in user_tweets and user_tweets["meta"]["result_count"] == 0):
        print("No new tweets found.")
        return

    # Init Google Docs API
    gd_service = pa.build('docs', 'v1')

    # Archive pun tweets to Google Doc
    pa.archive_tweets(gd_service, user_tweets)
    return


if __name__ == "__main__":    
    main()