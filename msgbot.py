import os
import time
import json
from slackclient import SlackClient

# TODO: Restructure the globals and __main__ portion of this file
# into classes and object instantiation. Make everything cleaner.

class MsgBotUserConfig(object):
    def __init__(self, bot_client, cfg_filename = os.getcwd() + os.path.normpath('/msgbotuserconfig.json')):
        self._cfg_filename = cfg_filename
        self._template = {
            'color'  : '0000ff', # default Blue
            'session': None,
        }
        self._valid_config_options = [
            'token',
            'fallback',
            'color',
            'thumb_url',
            'author_name',
            'author_icon',
            'image_url',
            'footer',
            'footer_icon',
            'ts'
        ]

        self._bot_client = bot_client

        # Try to open the config file. If it fails, create an empty config
        try:
            with open(cfg_filename) as cfg_file:
                self._config = json.load(cfg_file)
            for user_id in self._config:
                if self._config[user_id].get('token'):
                    self._config[user_id]['session'] = SlackClient(self._config[user_id]['token'])
                    try:
                        self._config[user_id]['session'].rtm_connect()
                    except:
                        self._config[user_id]['session'] = None
        except:
            print 'Error loading configuration from file: {0}. Using empty config.'.format(cfg_filename)
            self._config = {}

    def __getitem__(self, i):
        return self._config[i]

    def __str__(self):
        s = ''
        s += '\n'
        s += '========================================\n'
        s += '= User Configuration\n'
        s += '========================================\n'
        for user_id in self._config:
            username = (u.name for u in self._bot_client.server.users if user_id==u.id).next()
            s += '  {0} ({1})\n'.format(user_id, username)
            for key in self._config[user_id]:
                s += '    `- {0}: {1}\n'.format(key, self._config[user_id][key])
        s += '\n'
        return s

    # If you need access to the underlying dictionary, use the property 'config'
    # Otherwise, the individual's config dictionaries are accessible via __getitem__
    @property
    def config(self):
        return self._config

    def WriteConfig(self):
        cfg = self._config.copy()
        for id in cfg:
            try:
                cfg[id] = self._config[id].copy()
                cfg[id].pop('session')
            except:
                pass
        try:
            with open(self._cfg_filename, 'wb') as f:
                json.dump(cfg, f)
        except Exception as e:
            print 'Error saving configuration: {0}'.format(e)

    def LoadUserConfigJson(self, user_id, json_cfg):
        try:
            #parse income json for new config
            cfg = json.loads(json_cfg);
            #save off token and session so we can apply them post-import
            sc = user_config[user]['session']
            t = user_config[user]['token']

            #set config to loaded values
            self._config[user_id] = cfg;
            self._config[user_id]['session'] = sc #restore session we just blew away
            self._config[user_id]['token'] = t #restore token we just blew away
        except Exception as e:
            print 'Error loading configuration for user {0}: {1}'.format(user_id, e)

    def AddUser(self, user_id):
        self._config[user_id] = {}
        for key in self._template:
            self._config[user_id][key] = self._template[key]
            self.WriteConfig()

    def IsPresent(self, user_id):
        return user_id in self._config

    def HandleConfig(self, user_id, config_key, config_val):
        if config_key not in self._valid_config_options:
            return False

        self._config[user_id][config_key] = config_val.translate(None, '<>')
        if config_key == 'token':
            self._config[user_id]['session'] = SlackClient(self._config[user_id]['token'])
            try:
                self._config[user_id]['session'].rtm_connect()
            except:
                self._config[user_id]['session'] = None

        self.WriteConfig()

        return True

    def HandleDelete(self, user_id, config_key):
        if config_key not in self._config[user_id] or config_key == 'session':
            return False

        self._config[user_id].pop(config_key)

        self.WriteConfig()
        return True

# msgbot's ID as an environment variable
BOT_ID = SLACK_BOT_ID
BOT_TOKEN = SLACK_BOT_TOKEN
BOT_KEYPHRASE = SLACK_BOT_KEYPHRASE

if not BOT_ID:
    BOT_ID = os.environ.get("BOT_ID")

if not BOT_TOKEN:
    BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')

if not SLACK_BOT_KEYPHRASE:
    SLACK_BOT_KEYPHRASE = 'msgbot'

botsc = SlackClient(BOT_TOKEN)
user_config = MsgBotUserConfig(botsc)

def attempt_delete(user, ts, channel):
    if not user_config[user].get('session'):
        return
    sc = user_config[user]['session']
    sc.api_call("chat.delete", channel = channel, ts = ts, as_user=True)

def attempt_postMessage(user, channel, att):
    if not user_config[user].get('session'):
        return
    sc = user_config[user]['session']
    print att
    sc.api_call("chat.postMessage",
        type = 'message',
        channel = channel,
        as_user = True,
        attachments = json.dumps(att)
    )

def handle_message(msg, user, ts, channel):
    """
        Receives message directed at the bot and formats them accordingly.
    """
    # Add the user
    if not user_config.IsPresent(user):
        user_config.AddUser(user)
        print user_config


    # Check for '/config'
    if msg.startswith('/config'):

        # we need pure ascii to use .translate with the deletechars argument
        opt = [o.encode('utf-8') for o in msg.split()]
        if len(opt) < 3:
            return

        if user_config.HandleConfig(user, opt[1], ' '.join(opt[2:])):
            attempt_delete(user, ts, channel)
        return

    # Check for '/delete'
    if msg.startswith('/delete'):
        opt = [o.encode('utf-8') for o in msg.split()]
        print opt
        if len(opt) < 2:
            return

        if user_config.HandleDelete(user, opt[1]):
            attempt_delete(user, ts, channel)
        return

    # Check for '/dump'
    if msg.startswith('/dump'):
        att = {}

        for key in user_config[user]:
            if key in ['session', 'token']:
                continue
            att[key] = user_config[user][key]

        msg = json.dumps(att)

        attempt_delete(user, ts, channel)

    # Check for '/load'
    if msg.startswith('/load'):
        try:
            cfg = msg[5:];
            user_config.LoadUserConfigJson(user, cfg)

            #if we got here, the json.load call worked so delete the message and cut out.
            attempt_delete(user, ts, channel)

            return
        except Exception as ex:
            #if we failed, go ahead and usurp the message and drop down into printing it below
            msg = "Unable to load configuration from JSON.\nEnsure valid JSON before trying again"

    # Check for '/print' - if exists, throw away original message and replace with string dump of current config
    if msg.startswith('/print'):
        msg = "" #clear out current msg param so we can pass it along into the normal message display below
        for key in user_config[user]:
            if key in ['token', 'session']: #don't print these
                continue

            #add a formatted line to the current message with the current
            #config key and it's value
            msg += ''.join([key, ": ", user_config[user][key], "\n"])

    # No config, so this is a normal message that should be formatted (or the result of a /print)
    fb = user_config[user].get('fallback')
    if not fb:
        fb = msg
    att = [
        {
        'text': msg,
        'fallback': fb,
        },
    ]
    for key in user_config[user]:
        if key in ['session']:
            continue
        att[0][key] = user_config[user][key]

    # Delete the original message
    attempt_delete(user, ts, channel)

    attempt_postMessage(user, channel, att)

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and output['text'].startswith(BOT_KEYPHRASE):
                username = (u.name for u in botsc.server.users if output['user'] == u.id).next()
                print '<{0}> {1}: {2}'.format(output['channel'], username, output['text'].encode('utf-8'))
                # return text after the msgbot text, leading whitespace removed
                return output['text'][len(BOT_KEYPHRASE):].strip(),\
                       output['user'],\
                       output['ts'],\
                       output['channel']
    return None, None, None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if botsc.rtm_connect():
        print "msgbot connected and running!"
        while True:
            msg, user, ts, channel = parse_slack_output(botsc.rtm_read())
            if msg and user and ts and channel:
                handle_message(msg, user, ts, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print "Connection failed. Invalid Slack token or bot ID?"
