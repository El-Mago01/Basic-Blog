from flask import abort, Flask, render_template, request, redirect, url_for
import json
import os
from typing import Union

POST_STORAGE_LOC = 'data/'
IMAGE_STORAGE_LOC = 'static/images/uploads/'
app = Flask(__name__)

class BlogCorruption(Exception):
    pass

class InternalServerError(Exception):
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
        self.__ids_in_use = {}
        self.__cache_is_valid = True
        try:
            if os.path.exists(self.__storage):
                self.__json_fetch()  # make the cache and __ids_in_use valid again
            else:
                with open(self.__storage, 'w') as f:
                    f.write("")
        except InternalServerError as e:
            self.__cache_is_valid = False
            raise InternalServerError(f"Can not read JSON file. Please check path: {self.__storage}")

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
                return post.get("id")
        return -1

    def get_post(self, post_id)-> Union[dict, None]:
        if isinstance(self.__cache, list):
            for post in self.__cache:
                if post["id"] == post_id:
                    return post
        return None

    def __json_fetch(self):
        try:
            with open(self.__storage, 'r') as f:
                json_blogs = f.read()
        except (FileNotFoundError, OSError):
            self.__cache_is_valid = False
            raise InternalServerError(f"Can not read JSON file. Please check path: {self.__storage}")
        self.__cache = json.loads(json_blogs)
        self.__cache_is_valid = True
        for i in range(len(self.__cache)):
            self.__ids_in_use[self.__cache[i]['id']] = i
        print(f"The ids: ", self.__ids_in_use)
        return True


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
            self.__cache_is_valid = False
            raise InternalServerError(f"Can not store JSON file. Please check path: {self.__storage}")

    def get_free_id(self)->int:
        if len(self.__ids_in_use) == 0:
            print("new_id", 0)
            self.__ids_in_use = {1:0}
            return 1
        else:
            spot = 1
            while spot in self.__ids_in_use:
                spot += 1
            self.__ids_in_use[spot] = 'reserved'
            print("The ids in use: ", self.__ids_in_use)
            return spot

    def set(self, new_post: dict)->int:
        if not self.__cache_is_valid:
            self.__json_fetch()
        if isinstance(new_post, dict):
            # if the received post contains an id. Ignore id, find a free one
            # and check duplicate. If duplicate, don't store.
            existing_post_id = self.post_exists(new_post)
            if existing_post_id != -1:
                # This is the case that the post was already
                # existing with the exact same content, author
                # title. perhaps an overwrite. Treat this as
                # an overwrite:
                self.delete(existing_post_id)
            new_id = self.get_free_id()
            new_post["id"] = new_id
            post_image = new_post.get("image",None)
            print(f"Image of post to be added: {post_image}, {type(post_image)}")
            if isinstance(post_image, str) or post_image is None:
                if isinstance(post_image,str):
                    new_post['image'] = post_image
                else:
                    new_post['image'] = ""
            else:
                extension = post_image.filename.split('.')[-1]
                image_name = IMAGE_STORAGE_LOC + str(new_id) + new_post['author'] +"." + extension
                post_image.save(image_name)
                new_post["image"] = str(new_id) + new_post["author"] + "." + extension
            self.__cache.append(new_post)
            self.__ids_in_use[new_id] = len(self.__cache)-1
            self.__json_store()
            return new_id
        else:
            return -1


    def delete(self, post_id, keep_image:bool=False):
        """
           Delete a post from the JSON file.
           Fetch the existing blogs and find the element
           to be deleted. Pop it from the list and
           Store the updated blog list in the JSON file
           :param post_id : int
           :param keep_image : bool
           :return:
       """
        if not self.__cache_is_valid:
            self.__json_fetch()
        print(f"Attempting to delete post with id:{post_id}")
        for ind in range(len(self.__cache)):
            if self.__cache[ind].get("id") == post_id:
                # also remove any image if stored
                if self.__cache[ind].get('image',"") != "" and keep_image == False:
                    self.__delete_image(IMAGE_STORAGE_LOC + self.__cache[ind].get('image'))
                # Free up the 'id' of the post
                del self.__ids_in_use[post_id]
                self.__cache.pop(ind)
                self.__json_store()
                print("Post Deleted")
                return True
        return False

    def __delete_image(self, filename:str)->bool:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                raise InternalServerError(f"Can not remove image file. Please check path: {self.__storage}")
            return True
        return False

    def get_all_posts(self)->list:
        if not self.__cache_is_valid:
            self.__json_fetch()
        return self.__cache

    def __str__(self):
        if not self.__cache_is_valid:
            self.__json_fetch()
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
def get(post_id):
    print(f"User performed a GET request on /post/{post_id}")
    if not isinstance(post_id, int):
        abort(400,description="ID must be a number", post_id=post_id)
    try:
        post_id = int(post_id)
    except InternalServerError:
        print("Alarm - An Internal Server Error was raised. Please check json file or image file storages")
        abort(500, description="Internal Server error. Try again later.")
    post = blog.get_post(post_id)
    if post:
        return render_template('one_post.html', blog_name=blog.get_name(), post=post)
    else:
        abort(404, description="ID not found", post_id=post_id)

@app.route('/delete/<int:post_id>', methods=['GET'])
def delete(post_id):

    print(f"User performed a DELETE request with arg {post_id}")
    try:
        post_to_delete = int(post_id)
    except (KeyError, ValueError):
        print(f"User performed a DELETE request {post_id}, but a wrong id was provided")
        abort(404, description=f"A wrong id was provided: ", post_id=post_id)
    try:
        result = blog.delete(post_to_delete)
    except InternalServerError as e:
        print(f"Could not delete post {post_to_delete} due to: {e}")
        abort(500, description=f"We encountered an internal problem. Try again later.", post_id=post_to_delete)
    if result:
        print(f"Post  {post_to_delete} deleted")
        return render_template('index.html', blog_name=blog.get_name(), posts=blog.get_all_posts())
    abort(404, description=f"A wrong id was provided: {post_to_delete}")


@app.route('/update/<int:post_id>', methods=['GET', 'POST'])
def update(post_id):
    # Fetch the blog posts from the JSON file
    post = blog.get_post(post_id)
    print(f"User performed a {request.method} request with arg {post_id}")
    if post is None:
        # Post not found
        return "Post not found", 404

    if request.method == 'POST':
        id_to_update = post_id
        title = request.form.get('title')
        author = request.form.get('author')
        content = request.form.get('content')
        new_image = request.files.get('image',None)
        cur_image = request.form.get('current_image',None)
        if title == "" or author == "" or len(title) < 4 or len(author) < 3:
            abort(400, description="Title and/or author was not provided or was too short")
        upd_post = {"id": id_to_update, "title": title, "author": author, "content": content}
        if new_image:
            upd_post["image"] = new_image
        else:
            upd_post["image"] = cur_image
        blog.delete(id_to_update,keep_image=True)
        new_id=blog.set(upd_post)
        if new_id == id_to_update:
            print(f"Post with id: {id_to_update} updated")
        else:
            print(f"Post with id: {id_to_update} updated. Now stored under id {new_id}")
        return render_template('index.html', blog_name=blog.get_name(), posts=blog.get_all_posts())
    # Else, it's a GET request
    # So display the update.html page
    return render_template('update.html', blog_name=blog.get_name(), post=post)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'GET':
        return render_template("add.html")
    print(f"User performed an ADD request with title {request.form.get('title',"Not provided")}")
    try:
        title = request.form['title']
        author = request.form['author']
        content = request.form.get('content', "The title says it all")
        image = request.files.get('image',None)
        if title == "" or author == "" or len(title) < 4 or len(author) < 3:
            abort(400, description="Title and/or author was not provided or was too short")
    except KeyError:
        print("User performed an add request but no title and/or author was provided")
        abort(404, description="No title/author received")
    new_post = {"title": title, "author": author, "content": content}
    if image:
        new_post["image"] = image
    # print(dir(image))
    new_id=blog.set(new_post)
    print(f"New Post with id: {new_id} added")
    posts = blog.get_all_posts()
    return render_template('index.html', blog_name=blog.get_name(), posts=posts)

@app.errorhandler(400)
def bad_user_request400(error):
    return render_template("error.html", code=400, message=error.description), 400

@app.errorhandler(404)
def bad_user_request404(error):
    return render_template("error.html", code=404, message=error.description), 404

@app.errorhandler(405)
def bad_user_request405(error):
    return render_template("error.html", code=405, message=error.description), 405

@app.errorhandler(500)
def internal_server_error500(error):
    return render_template("error.html", code=500, message=error.description), 500


def main():
    print("==========================================================================")
    initial_blog_posts = [
        {"id": 1, "author": "Frank Rijkaard", "title": "My first goal", "content": "This was my first goal for Ajax-1.", "image":""},
        {"id": 2, "author": "Marco van Basten", "title": "My best memory @AJAX", "content": "The jersey is simply amazing!", "image":""},
    ]
    if len(blog.get_all_posts()) == 0:
        for initial_post in initial_blog_posts:
            try:
                stored_id = blog.set(initial_post)
            except InternalServerError as e:
                return render_template(url_for('static'+"/error.html"), code=500, message=e)
            print("Stored initial post with id ", stored_id)
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == '__main__':
    main()
