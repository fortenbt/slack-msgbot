# msgbot

This is a Slack bot written in python, utilizing the python library located
here: https://github.com/slackhq/python-slackclient

This bot is meant to facilitate the creation of custom messages with
attachments directly from Slack's message bar.

### /print
**Usage**

`msgbot /print`


### /config

**Usage**

`msgbot /config [option] |value|`

Configuration Options:

* fallback (short message for notification screen, defaults to the message itself)
* color (formatted like #RRGGBB)
* thumb_url  (a thumbnail to be shown to the right of the message, like the url of dickbutt, for instance)
* author_name (name displayed at the top of the message)
* author_icon (the url of an icon to be displayed next to the author name (dickbutt))
* footer (text displayed below the message)
* footer_icon (url of an icon to be displayed next to the footer)
* ts (timestamp associated with the message)

