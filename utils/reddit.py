import random

import praw


class RedditInstance:

    def __init__(self, client_id, client_secret, username, password):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent="BAROIS",
        )

    def showerthoughs_random(self):
        sub = self.reddit.subreddit('showerthoughs')
        # posts = sub.random()

        posts = [post for post in sub.top(limit=100, time_filter="year")]
        random_post_number = random.randint(0, len(posts) - 1)
        random_post = posts[random_post_number]

        showerthought_text = random_post.title

        if len(random_post.selftext) != 0:
            showerthought_text += '\n\n' + random_post.selftext

        return showerthought_text

    def memes_random(self):
        sub = self.reddit.subreddit('memes+dankmemes')
        random_post = sub.random()

        # posts = [post for post in sub.top(limit=100, time_filter="year")]
        # random_post_number = random.randint(0, len(posts) - 1)
        # random_post = posts[random_post_number]

        return random_post.url

    def subreddit_random(self, subreddit, option='link'):
        sub = self.reddit.subreddit(subreddit)
        # random_post = sub.random()

        posts = [post for post in sub.top(limit=100, time_filter="year")]
        random_post_number = random.randint(0, len(posts) - 1)
        random_post = posts[random_post_number]

        if option == 'text':
            post_text = random_post.title

            if len(random_post.selftext) != 0:
                post_text += '\n\n' + random_post.selftext

            return post_text
        else:
            return random_post.url
