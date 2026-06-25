from flask import Flask, render_template, request, jsonify
import json
import os
from typing import Union

POST_STORAGE_LOC = 'data/'
app = Flask(__name__)

class BlogCorruption(Exception):
    pass

# class BlogPost:
#     def __init__(self, author, title, content, this_blog:Blog):
#         self.__id = -1
#         self.__author = author
#         self.__title = title
#         self.__content = content
#         self.__blog_container = this_blog
#
#     def get(self)->dict:
#         post = {'id': self.__id, 'author': self.__author, 'title': self.__title, 'content': self.__content}
#         return post
#
#     def get_id(self):
#         return self.__id
#
#     def set_id(self, new_id):
#         self.__id = new_id
#
#     def __str__(self):
#         return f"{self.__id} - {self.__author} - {self.__title}\n - {self.__content}"
#
#     def __repr__(self):
#         return f"{self.__id} - {self.__author} - {self.__title}\n - {self.__content}"

class Blog:

    @classmethod
    def is_duplicate(cls, new_post:dict, existing_post:Union[dict,None]) -> bool:
        if isinstance(existing_post, dict):
            return False
        if (new_post['title'] == existing_post['title'] and
                new_post['author'] == existing_post['author'] and
                new_post['content'] == existing_post['content']):
            return True
        return False

    def __init__(self, name):
        self.__name = name
        self.__cache = []
        self.__cache_valid = False
        self.storage=POST_STORAGE_LOC + self.__name + ".json"

    def get_name(self):
        return self.__name

    def __json_fetch(self)->list:
        if os.path.exists(self.storage):
            with open(self.storage, 'r') as f:
                json_blogs = f.read()
                self.__cache = json.loads(json_blogs)
                self.__cache_valid = True

    def post_exists(self, new_post):
        if not self.__cache_valid:
            self.__json_fetch() # make the cache valid again
        for post in self.__cache:
            if ((post.get("title","a") == new_post.get("title",'b') and
                    post.get('content','a') == new_post.get('content','b')) and
                    post.get('author','a') == new_post.get('author','b')):
                return True
        return False

    def get_post(self, id)-> Union[dict, None]:
        if not self.__cache_valid:
            self.__json_fetch()  # make the cache valid again
        if isinstance(self.__cache, list):
            for post in self.__cache:
                if post["id"] == id:
                    return post
        return None

    def __json_store(self, new_post:dict):
        """
        Append a post (as dict) in the json file.
        If the file doesn't exist, create it.
        Otherwise, fetch the existing blogs and append
        the new one
        Store the combination of blog posts in the json file
        :param blog_list:
        :return:
        """
        # In case the json file exists:
        #    Check if the id of the blog is not already used
        #        if it is, check if it is not duplicated
        #        if not change id, store blog and return the new id
        #    else
        #        use the provided id to store the blog
        if not self.__cache_valid:
            self.__json_fetch()  # make the cache valid again
        if self.post_exists(new_post):
            return False
        self.__cache.append(new_post)
        json_str = json.dumps(self.__cache)

        with open(self.storage, 'w') as f:
            f.write(json_str)
            self.__cache_valid = False
            return True

    def get_free_id(self)->int:
        if not self.__cache_valid:
            self.__json_fetch()  # make the cache valid again
        if len(self.__cache) == 0:
            return 0
        else:
            if isinstance(self.__cache, list):
                new_id = self.__cache[-1:][0].get('id', 0) + 1
                print("neW", new_id)
                return new_id
            else:
                raise BlogCorruption("The blog is corrupted")

    def set(self, posts: list)->bool:
        if isinstance(posts, list):
            for a_post in posts:
                cur_id = a_post.get("id", None)
                if cur_id is None: # Within the received post, there is no id yet
                    cur_id = self.get_free_id()
                else: # if the received post contains an id. Check duplicate.
                    existing_post = self.get_post(cur_id)
                    if existing_post is None:
                        cur_id = self.get_free_id()
                    else:
                        if not self.is_duplicate(a_post, existing_post):
                            # update received id in case received post was not stored yet
                            cur_id = self.get_free_id()
                        else:
                            return False
                a_post["id"] = cur_id
                self.__json_store(a_post)
            return True
        else:
            return False

    def get_all_posts(self)->list:
        if not self.__cache_valid:
            self.__json_fetch()  # make the cache valid again
        return self.__cache

    def get_post(self, id):
        if not self.__cache_valid:
            self.__json_fetch()  # make the cache valid again
        if isinstance(self.__cache, list):
            for post in self.__cache:
                if post.get("id", None) == id:
                    return post
        return None

    def __str__(self):
        if not self.__cache_valid:
            self.__json_fetch()  # make the cache valid again
        posts_str = ""
        if isinstance(self.__cache, list):
            for post in self.__cache:
                for key, value in post.items():
                    posts_str += f"{key}: {value} - "
                posts_str = blposts_strog_posts_str[:-3]
                posts_str += "\n======================================================\n"
        return posts_str

my_blog = Blog("We Love Ajax")

@app.route('/')
def index():
    print(my_blog.get_all_posts())
    return render_template('index.html', title=my_blog.get_name(), posts=my_blog.get_all_posts())

def main():
    print("==========================================================================")
    initial_blog_posts = [
        {"id": 1, "author": "John Doe", "title": "First Post", "content": "This is my first post."},
        {"id": 2, "author": "Jane Doe", "title": "Second Post", "content": "This is another post."}
    ]
    my_blog.set(initial_blog_posts)
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == '__main__':
    main()