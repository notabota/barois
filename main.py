import os
import threading
import time

import org_fbchat as fbchat
from org_fbchat.models import *
import json
from dotenv import load_dotenv

from utils.reddit import RedditInstance
from utils.api import API

from io import StringIO
from contextlib import redirect_stdout
from func_timeout import func_timeout, FunctionTimedOut
import math
from pytube import YouTube, Search


def convert_size(size_bytes, i=2):
    if size_bytes == 0:
        return "0B"
    # size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    # i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return s


load_dotenv()

EMAIL = os.environ['EMAIL']
PASS = os.environ['PASS']
REDDIT_CLIENT_ID = os.environ['REDDIT_CLIENT_ID']
REDDIT_CLIENT_SECRET = os.environ['REDDIT_CLIENT_SECRET']
REDDIT_USERNAME = os.environ['REDDIT_USERNAME']
COMMAND_PREFIX = '-b'

reddit = RedditInstance(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, PASS)


class SetInterval:
    def __init__(self, action, delay=0, interval=1, wait=0, **kwargs):
        self.delay = delay
        self.interval = interval
        self.wait = wait
        self.action = action
        self.stopEvent = threading.Event()
        self.kwargs = kwargs

    def __setInterval(self):
        nextTime = delayTime = time.time() + self.delay
        while not self.stopEvent.wait(delayTime - time.time()):
            while not self.stopEvent.wait(nextTime - time.time()):
                nextTime += self.interval
                self.action(**self.kwargs)

    def start(self):
        IntervalThread = threading.Thread(target=self.__setInterval)
        IntervalThread.start()
        t = threading.Timer(self.delay + self.interval * self.wait, self.cancel)
        t.start()

    def cancel(self):
        self.stopEvent.set()


thread = {}


class BAROIS(fbchat.Client):

    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None,
                  thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):

        def sendRemoteVoiceClips(url, thread_id, thread_type):
            def sendFunc():
                self.sendRemoteVoiceClips(url, thread_id=thread_id, thread_type=thread_type)

            send_inter = SetInterval(action=sendFunc)
            send_inter.start()

        def sendLocalVoiceClips(path, thread_id, thread_type, delete=False):
            def sendFunc():
                self.sendLocalVoiceClips(path, thread_id=thread_id, thread_type=thread_type, delete=delete)

            send_inter = SetInterval(action=sendFunc)
            send_inter.start()

        def sendRemoteFiles(url, thread_id, thread_type):
            def sendFunc():
                self.sendRemoteVoiceClips(url, thread_id=thread_id, thread_type=thread_type)

            send_inter = SetInterval(action=sendFunc)
            send_inter.start()

        def sendLocalFiles(url, thread_id, thread_type, delete=False):
            def sendFunc():
                self.sendLocalFiles(url, thread_id=thread_id, thread_type=thread_type, delete=delete)

            send_inter = SetInterval(action=sendFunc)
            send_inter.start()

        def send(send_message, thread_id, thread_type):
            def sendFunc():
                self.send(send_message, thread_id=thread_id, thread_type=thread_type)

            send_inter = SetInterval(action=sendFunc)
            send_inter.start()

        global thread

        if author_id == self.uid:
            return

        # fbchat.log.info("{} from {} in {}".format(message_object, thread_id, thread_type.name))

        message_text = message.split()

        # print(thread)
        # print(type(thread_id))
        if thread_id not in thread:
            thread[thread_id] = {}

        if author_id not in thread[thread_id]:
            thread[thread_id][author_id] = {
                'listen': False
            }

        if not thread[thread_id][author_id]['listen'] and len(message_text) > 1 and message_text[0] == COMMAND_PREFIX:
            command = message_text[1]
            if command == 'memes':
                sendRemoteFiles(reddit.memes_random(), thread_id=thread_id, thread_type=thread_type)
            elif command == 'showerthoughts':
                send(Message(text=reddit.showerthoughs_random()), thread_id=thread_id, thread_type=thread_type)
            elif command == 'uwu':
                if len(message_text) == 2:
                    send(Message(text="What uwu"), thread_id=thread_id, thread_type=thread_type)
                    return

                uwuify_text = ' '.join(message_text[2:])
                uwuifier = API()
                send(Message(text=uwuifier.uwuaas(uwuify_text)), thread_id=thread_id, thread_type=thread_type)

            elif command == 'vanmau':
                if len(message_text) == 2:
                    send(Message(text="What vammau"), thread_id=thread_id, thread_type=thread_type)
                    return

                baivanmau = ' '.join(message_text[2:])
                vanmau = API()
                send(Message(text=vanmau.vanmau(baivanmau)), thread_id=thread_id, thread_type=thread_type)

            elif command == 'ytb':

                def ytb():

                    if len(message_text) == 2:
                        send(Message(text="What type"), thread_id=thread_id, thread_type=thread_type)
                        return

                    ytb_type = message_text[2]

                    if ytb_type not in ['video', 'audio']:
                        send(Message(text="video or audio"), thread_id=thread_id, thread_type=thread_type)
                        return

                    if len(message_text) == 3:
                        send(Message(text="What video search?"), thread_id=thread_id, thread_type=thread_type)
                        return

                    send(Message(text="Requesting"), thread_id=thread_id, thread_type=thread_type)

                    query = message_text[3:]
                    search = Search(query)
                    result = search.results[0]
                    link = result.watch_url
                    title = result.title
                    yt = YouTube(link)

                    get_yt = None
                    if ytb_type == 'audio':
                        get_yt = yt.streams.get_audio_only()
                    elif ytb_type == 'video':
                        get_yt = yt.streams.get_highest_resolution()

                    get_yt_filesize = convert_size(get_yt.filesize)

                    if convert_size(get_yt.filesize) > 25:
                        send(Message(text=f'"{title}": {get_yt_filesize}MB exceed 25MB size limit'),
                             thread_id=thread_id,
                             thread_type=thread_type)
                    else:
                        send(Message(text=f'Sending'),
                             thread_id=thread_id,
                             thread_type=thread_type)
                        get_yt_path = get_yt.download()
                        if ytb_type == 'audio':
                            audio_get_yt_path = '.'.join(get_yt_path.split('.')[:-1] + ['mp3'])
                            os.rename(get_yt_path, audio_get_yt_path)
                            get_yt_path = audio_get_yt_path
                            sendLocalVoiceClips(
                                get_yt_path,
                                thread_id=thread_id, thread_type=thread_type, delete=True)


                        elif ytb_type == 'video':
                            sendLocalFiles(
                                get_yt_path,
                                thread_id=thread_id, thread_type=thread_type, delete=True)

                        while os.path.isfile(get_yt_path):
                            try:
                                os.remove(get_yt_path)
                            except Exception as e:
                                time.sleep(30)

                inter = SetInterval(action=ytb)
                inter.start()

            elif command == 'remind':
                if len(message_text) == 2:
                    send(Message(text="What time?"), thread_id=thread_id, thread_type=thread_type)
                    return

                sched_time = message_text[2]
                if not sched_time.isdigit():
                    send(Message(text="Wrong time format"), thread_id=thread_id,
                         thread_type=thread_type)
                else:
                    thread[thread_id][author_id]['listen'] = True
                    thread[thread_id][author_id]['mode'] = 'remind'
                    thread[thread_id][author_id]['sched_time'] = int(sched_time)
                    send(Message(text="Send text to remind"), thread_id=thread_id,
                         thread_type=thread_type)

            elif command == 'spam':
                if len(message_text) == 2:
                    send(Message(text="What python?"), thread_id=thread_id, thread_type=thread_type)
                    return

                name = ' '.join(message_text[2:])

                fetch_thread = self.fetchThreadInfo(thread_id)[thread_id]

                def spamming(**kwargs):
                    send(
                        Message(
                            text="Spamming @" + name,
                            mentions=[Mention(participants, offset=9, length=len(name) + 1)]
                        ),
                        thread_id=participants,
                        thread_type=ThreadType.USER,
                    )

                participants_info = self.fetchUserInfo(*fetch_thread.participants)

                print(participants_info)

                for participants in participants_info:
                    if name == participants_info[participants].name:
                        send(
                            Message(
                                text="Spamming @" + name,
                                mentions=[Mention(participants, offset=9, length=len(name) + 1)]
                            ),
                            thread_id=thread_id,
                            thread_type=thread_type,
                        )

                        inter = SetInterval(interval=5, wait=5, action=spamming)
                        inter.start()

                        break


            elif command == 'reddit':
                if len(message_text) == 2:
                    send(Message(text="What reddit?"), thread_id=thread_id, thread_type=thread_type)
                    return

                subreddit = message_text[2]
                if len(message_text) == 4 and message_text[3] == 'images':
                    sendRemoteFiles(reddit.subreddit_random(subreddit=subreddit, option='images'),
                                    thread_id=thread_id,
                                    thread_type=thread_type)

                else:
                    send(Message(text=reddit.subreddit_random(subreddit=subreddit)),
                         thread_id=thread_id,
                         thread_type=thread_type)
            elif command == 'py':
                if len(message_text) == 2:
                    send(Message(text="What python?"), thread_id=thread_id, thread_type=thread_type)
                    return

                program = ' '.join(message_text[2:])

                def thread_execute():

                    def execute():
                        f = StringIO()
                        with redirect_stdout(f):
                            exec(program)

                        return f.getvalue()

                    try:
                        s = func_timeout(10, execute)
                    except FunctionTimedOut:
                        s = 'Program could not complete within 5 seconds and was terminated.\n'
                    except Exception as e:
                        s = str(e)

                    if len(s) != 0:
                        send(Message(text=s), thread_id=thread_id,
                             thread_type=thread_type)
                    else:
                        send(Message(text='program print nothing'), thread_id=thread_id,
                             thread_type=thread_type)

                send_inter = SetInterval(action=thread_execute)
                send_inter.start()

            else:
                send(Message(text='Tf you talking about ' + command), thread_id=thread_id,
                     thread_type=thread_type)

        elif thread[thread_id][author_id]['listen']:

            thread_data = thread[thread_id][author_id]
            print(thread_data)
            mode = thread_data['mode']
            if mode == 'remind':
                def remind_group(**kwargs):
                    send(Message(text=message_text), thread_id=thread_id,
                         thread_type=thread_type)

                inter = SetInterval(delay=thread_data['sched_time'], action=remind_group)
                inter.start()

            thread[thread_id][author_id]['listen'] = False


client = BAROIS(EMAIL, PASS)
client.listen()

# client = fbchat.Client(EMAIL, PASS,
#                        session_cookies=SESSION_COOKIES)
#
# # Fetches a list of the 20 top threads you're currently chatting with
# threads = client.fetchThreadList(limit=3)
#
# print(threads)
