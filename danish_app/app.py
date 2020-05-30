import os
import logging
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from danish_app import DanishApp

# Initialize a Flask app to host the events adapter
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(os.environ["SLACK_SIGNING_SECRET"], "/slack/events", app)

# Initialize a Web API client
slack_web_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

# For simplicity we'll store our app data in-memory with the following data structure.
# danish_apps_sent = {"channel": {"user_id": DanishApp}}
danish_apps_sent = {}


def register_with_danish(user_id: str, channel: str):
    # Create a new onboarding tutorial.
    danish_app = DanishApp(channel)

    # Get the onboarding message payload
    message = danish_app.get_message_payload()

    # Post the onboarding message in Slack
    response = slack_web_client.chat_postMessage(**message)

    # Capture the timestamp of the message we've just posted so
    # we can use it to update the message after a user
    # has completed an onboarding task.
    danish_app.timestamp = response["ts"]

    # Store the message sent in danish_apps_sent
    if channel not in danish_apps_sent:
        danish_apps_sent[channel] = {}
    danish_apps_sent[channel][user_id] = danish_app

@slack_events_adapter.on("message")
def message(payload):
    """Display the onboarding welcome message after receiving a message
    that contains "start".
    """
    event = payload.get("event", {})

    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")


    if text and text.lower() == "register":
        return register_with_danish(user_id, channel_id)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    app.run(port=3000)
