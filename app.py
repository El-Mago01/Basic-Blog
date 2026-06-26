from flask import Flask, render_template, request, jsonify
import json
import os
from typing import Union


POST_STORAGE_LOC = 'data/'
IMAGE_STORAGE_LOC = 'static/images/uploads'
app = Flask(__name__)

class BlogCorruption(Exception):
    pass

class StorageError(Exception):
    pass


class Blog:

    @classmethod
    def is_duplicate(cls, new_post:dict, existing_post:Union[dict,None]) -> bool:
        if not isinstance(existing_post, dict):
            return False
        if (new_post['title'] == existing_post['title'] and
                new_post['author'] == existing_post['author'] and
                new_post['content'] == existing_post['content']):
            return True
        return False

    def __init__(self, name):
        self.__name = name
        self.__cache = []
        self.__storage=POST_STORAGE_LOC + self.__name + ".json"
        self.__json_fetch()  # make the cache valid again

    def __contains__(self, an_id):
        for post in self.__cache:
            if post["id"] == an_id:
                return True
        return False

    def get_name(self):
        return self.__name

    def post_exists(self, new_post)-> int:
        for post in self.__cache:
            if (post.get("title","a") == new_post.get("title",'b') and
                    post.get('content','a') == new_post.get('content','b') and
                    post.get('author','a') == new_post.get('author','b')):
                return True
            return post.get("id", -1)
        return -1

    def get_post(self, post_id)-> Union[dict, None]:
        if isinstance(self.__cache, list):
            for post in self.__cache:
                if post["id"] == post_id:
                    return post
        return None

    def __json_fetch(self):
        if os.path.exists(self.__storage):
            with open(self.__storage, 'r') as f:
                json_blogs = f.read()
                self.__cache = json.loads(json_blogs)
                self.__cache_valid = True

    def __json_store(self):
        """
        Turn the cache into a json file
        Store the JSON file to the file for this specific blog
        :param
        """
        json_str = json.dumps(self.__cache)
        try:
            with open(self.__storage, 'w') as f:
                f.write(json_str)
        except (FileNotFoundError, OSError):
            raise StorageError(f"Can not store JSON file. Please check path: {self.__storage}")

    def get_free_id(self)->int:
        if len(self.__cache) == 0:
            print("new_id", 0)
            return 1
        else:
            for spot in range(1,len(self.__cache)+1):
                if not spot in self:
                    return spot
            return self.__cache[-1]["id"] + 1


    def set(self, posts: Union[list, dict])->bool:
        if isinstance(posts, dict):
            posts = [posts]
        if isinstance(posts, list):
            for a_post in posts:
                # if the received post contains an id. Ignore id, find a free one
                # and check duplicate. If duplicate, don't store.
                existing_post_id = self.post_exists(a_post)
                if existing_post_id != -1:
                    # This is the case that the post was already
                    # existing with the exact same content, author
                    # title. perhaps an overwrite. Treat this as
                    # an overwrite:
                    self.delete(existing_post_id)
                new_id = self.get_free_id()
                a_post["id"] = new_id
                post_image = a_post.get("image",None)
                if not (isinstance(post_image, str) or post_image is None):
                    print(type(post_image))
                    if post_image.filename != "":
                        image_name = IMAGE_STORAGE_LOC + str(new_id) + a_post['title']
                        post_image.save(image_name)
                        a_post["image"] = str(new_id) + a_post["title"]
                    else:
                        a_post['image'] = ""
                else:
                    a_post['image'] = ""
                self.__cache.append(a_post)
                self.__json_store()
            return new_id
        else:
            return -1

    def delete(self, post_id):
        """
           Delete a post from the JSON file.
           Fetch the existing blogs and find the element
           to be deleted. Pop it from the list and
           Store the updated blog list in the JSON file
           :param post_id : int
           :return:
       """
        print(f"Attempting to delete post with id:{post_id}")
        if isinstance(self.__cache, list):
            for index in range(len(self.__cache)):
                if self.__cache[index]["id"] == post_id:
                    # also remove any image if stored
                    if self.__cache[index].get('image',"") != "":
                        self.__delete_image(self.__cache[index]['image'])
                    self.__cache.pop(index)
                    self.__json_store()
                    print("Post Deleted")
                    return True
            return False
        raise BlogCorruption("The blog is corrupted on the JSON file."
                             f"Please consider deleting file {self.__storage}")

    def __delete_image(self, filename:str)->bool:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                return False
            return True
        return False

    def get_all_posts(self)->list:
        return self.__cache

    def __str__(self):
        posts_str = ""
        if isinstance(self.__cache, list):
            for post in self.__cache:
                for key, value in post.items():
                    posts_str += f"{key}: {value} - "
                posts_str = posts_str[:-3]
                posts_str += "\n======================================================\n"
        return posts_str

blog = Blog("We Love Ajax")

@app.route('/')
def index():
    print("A User landed on our page. He'll see the following blogs:")
    print(blog.get_all_posts())
    return render_template('index.html', blog_name=blog.get_name(), posts=blog.get_all_posts())

@app.route('/post/<int:post_id>')
def get_post(post_id):
    print(f"User performed a GET request on /post/{post_id}")
    if not isinstance(post_id, int):
        return render_template('fault_500.html')
    post = blog.get_post(post_id)
    return render_template('one_post.html', blog_name=blog.get_name(), post=post)

@app.route('/delete', methods=['POST'])
def delete_post():
    print(f"User performed a DELETE request with arg {request.form.get('id',-1)}")
    try:
        post_to_delete = int(request.form['id'])
    except KeyError:
        print(f"User performed a DELETE request {request.form.get('id_to_delete'),999}, but a wrong id was received")
        return render_template('fault_500.html')
    if not isinstance(post_to_delete, int):
        return render_template('fault_500.html')
    blog.delete(post_to_delete)
    print(f"Post  {post_to_delete} deleted")

    posts = blog.get_all_posts()
    return render_template('index.html', blog_name=blog.get_name(), posts=posts)

@app.route('/add', methods=['POST'])
def add_post():
    print(f"User performed an ADD request with title {request.form.get('title',"Not provided")}")
    try:
        title = request.form.get('title',"Blog without a title")
        author = request.form.get('author', "Anonymous")
        content = request.form.get('content', "The title says it all")
        image = request.files.get('image',None)

    except KeyError:
        print(f"User performed a DELETE request {request.form.get('id_to_delete'),999}, but a wrong id was received")
        return render_template('fault_500.html')
    new_post = {}
    new_post["title"] = title
    new_post["author"] = author
    new_post["content"] = content
    print(dir(image))
    if image:
        new_post["image"] = image.filename
    new_id=blog.set(new_post)
    print(f"New Post with id: {new_id} added")
    posts = blog.get_all_posts()
    return render_template('index.html', blog_name=blog.get_name(), posts=posts)

def main():
    print("==========================================================================")
    initial_blog_posts = [
        {"id": 1, "author": "Frank Rijkaard", "title": "My first goal", "content": "This was my first goal for Ajax-1.", "image":"Frank-Rijkaard.jpeg"},
        {"id": 2, "author": "Marco van Basten", "title": "My best memory @AJAX", "content": "The jersey is simply amazing!", "image":"Marco-van-Basten.avif"},
    ]
    blog.set(initial_blog_posts)
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == '__main__':
    main()