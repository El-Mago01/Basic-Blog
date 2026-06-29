import json
import os
from typing import Union
from flask import abort, Flask, render_template, request, url_for

POST_STORAGE_LOC = "data/"
IMAGE_STORAGE_LOC = "static/images/uploads/"
app = Flask(__name__)


class BlogCorruption(Exception):
    """Defining the BlogCorruption Exception"""
    pass


class InternalServerError(Exception):
    """Defining the InternalServerError Exception"""

    pass


class Blog:
    """
        Class Blog envelops the methods and data required to handled the whole Blog,
        including:
        - adding a new post
        - deleting a post
        - updating a post
        - displaying the posts as string
        - getting all available posts
        - storage to JSON file from related cached variable
        - fetching from JSON file and sync with related cached variable
        + self.__name => name of the blog with all posts
        + self.__cache => cached variable
        + self.__storage => the storage file in json format
        + self.__ids_in_use => the cached ids stored in JSON file. This should
                            improve Big-O for id-checking
        + self.__cache_is_valid => An indicator if the cache is valid
                                   Note, cache becomes invalid in case of
                                   a problem with the json file. E.g. when
                                   access rights are removed
    """
    def __init__(self, name):
        """
        The constructor of the Blog
        :param name: The name of the blog
        """
        self.__name = name
        self.__cache = []
        self.__storage = POST_STORAGE_LOC + self.__name + ".json"
        self.__ids_in_use = {}
        self.__likes = 0
        self.__cache_is_valid = True
        try:
            if os.path.exists(self.__storage):
                self.__json_fetch()  # make the cache and __ids_in_use valid again
            else:
                with open(self.__storage, "w") as f:
                    f.write("")
        except InternalServerError as e:
            self.__cache_is_valid = False
            raise InternalServerError(
                f"Can not read JSON file. Please check path: {self.__storage}"
            ) from e

    def __contains__(self, an_id):
        """
        Enables to see if a specific post id is stored in the Blog
        :param self:
        :param an_id:the id of the post to be checked
        :return: True if the post is found
        """
        for post in self.__cache:
            if post["id"] == an_id:
                return True
        return False

    def get_name(self):
        """
        Returns the name of the blog
        :param self:
        :return:
        """
        return self.__name

    def post_exists(self, new_post) -> int:
        """
        Verifies if a post with the same data is perhaps already stored in the Blog.
        This should prevent duplications
        :param self:
        :param new_post: The post to be checked if the fields are already in the
        Blog storage
        :return:
        """
        for post in self.__cache:
            if (
                post.get("title", "a") == new_post.get("title", "b")
                and post.get("content", "a") == new_post.get("content", "b")
                and post.get("author", "a") == new_post.get("author", "b")
            ):
                return post.get("id")
        return -1

    def get_post(self, post_id) -> Union[dict, None]:
        """
        From a provided id, return the post. N
        :param self:
        :param post_id:
        :return: None if the id is not found
                 the Post as Dict if the id is not found
        """
        if isinstance(self.__cache, list):
            for post in self.__cache:
                if post["id"] == post_id:
                    return post
        return None

    def __json_fetch(self):
        """
        Fetch all the posts from the json file and store it in the cached instance variable
        if the file is not accessible for whatever reason, the cache variable will be marked
        as invalid
        It will also update the cached "Ids in use" instance variable.
        :param self:
        :return:
        """
        try:
            with open(self.__storage, "r") as f:
                json_blogs = f.read()
        except (FileNotFoundError, OSError) as e:
            self.__cache_is_valid = False
            raise InternalServerError(
                f"Can not read JSON file. Please check path: {self.__storage}"
            ) from e
        self.__cache = json.loads(json_blogs)
        self.__cache_is_valid = True
        for i, post in enumerate(self.__cache):
            self.__ids_in_use[post["id"]] = i
        return True

    def __json_store(self):
        """
        Turn the cache into a json file
        Store the JSON file to the file for this specific blog
        :param
        """
        json_str = json.dumps(self.__cache)
        try:
            with open(self.__storage, "w") as f:
                f.write(json_str)
        except (FileNotFoundError, OSError) as e:
            self.__cache_is_valid = False
            raise InternalServerError(
                f"Can not store JSON file. Please check path: {self.__storage}"
            ) from e

    def get_free_id(self) -> int:
        """
        Returns the first free id available. I.e. if a post is deleted, the ID that
        that post had will become available.
        :param self:
        :return:
        """
        if len(self.__ids_in_use) == 0:
            print("new_id", 0)
            self.__ids_in_use = {1: 0}
            return 1
        spot = 1
        while spot in self.__ids_in_use:
            spot += 1
        self.__ids_in_use[spot] = "reserved"
        print("The ids in use: ", self.__ids_in_use)
        return spot

    def set(self, new_post: dict) -> int:
        """
        Insert a new post in the cache variable and call the json_store method
        to store the new post.
        In case the post contains an image, store the image in the correct folder.
        The image will get the Post-id together with the
        :param self:
        :param new_post:
        :return:
        """
        if not self.__cache_is_valid:
            self.__json_fetch() # make the cache valid again.
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
            new_post["likes"] = 0
            post_image = new_post.get("image", None)
            print(f"Image of post to be added: {post_image}, {type(post_image)}")
            if isinstance(post_image, str) or post_image is None:
                if isinstance(post_image, str):
                    new_post["image"] = post_image
                else:
                    new_post["image"] = ""
            else:
                extension = post_image.filename.split(".")[-1]
                image_name = (
                    IMAGE_STORAGE_LOC
                    + str(new_id)
                    + new_post["author"]
                    + "."
                    + extension
                )
                post_image.save(image_name)
                new_post["image"] = str(
                    new_id) + new_post["author"] + "." + extension
            self.__cache.append(new_post)
            self.__ids_in_use[new_id] = len(self.__cache) - 1
            self.__json_store()
            return new_id

        return -1

    def delete(self, post_id, keep_image: bool = False):
        """
        Delete a post from the JSON file.
        Fetch the existing blogs and find the element
        to be deleted. Pop it from the list and
        Store the updated blog list in the JSON file
        If the post contains an image, check keep_image variable to see
        if the image should be kept or not.
        :param post_id : int
        :param keep_image : bool
        :return:
        """
        if not self.__cache_is_valid:
            self.__json_fetch()
        print(f"Attempting to delete post with id:{post_id}")
        for ind, post in enumerate(self.__cache):
            if post["id"] == post_id:
                # also remove any image if stored
                if self.__cache[ind].get(
                        "image", "") != "" and not keep_image:
                    self.__delete_image(
                        IMAGE_STORAGE_LOC + self.__cache[ind].get("image")
                    )
                # Free up the 'id' of the post
                del self.__ids_in_use[post_id]
                self.__cache.pop(ind)
                self.__json_store()
                print("Post Deleted")
                return True
        return False

    def __delete_image(self, filename: str) -> bool:
        """
        This internal method is to remove any image if the post contained one
        :param self:
        :param filename:
        :return:
        """
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError as e:
                raise InternalServerError(
                    f"Can not remove image file. Please check path: {
                        self.__storage}") from e
            return True
        return False

    def like(self, post_id: int) -> int:
        post_to_like = self.get_post(post_id)
        current_likes = 0
        if post_to_like:
            current_likes = post_to_like['likes']
            current_likes += 1
            post_to_like['likes'] = current_likes
            self.__json_store()
        return current_likes

    def get_all_posts(self) -> list:
        """
        Return all cached posts in list format
        :param self:
        :return:
        """
        if not self.__cache_is_valid:
            self.__json_fetch()
        return self.__cache

    def __str__(self):
        """
        print the available posts as string. For images, the
        :param self:
        :return:
        """
        if not self.__cache_is_valid:
            self.__json_fetch()
        posts_str = ""
        if isinstance(self.__cache, list):
            for post in self.__cache:
                for key, value in post.items():
                    posts_str += f"{key}: {value} - "
                posts_str = posts_str[:-3]
                posts_str += (
                    "\n======================================================\n"
                )
        return posts_str

blog = Blog("We Love Ajax")

def check_received_post_id(post_id:str)-> int:
    try:
        post_id = int(post_id)
    except ValueError:
        print(
            "Client provided a wrong post-id"
        )
        abort(404, description="ID must be a number", post_id=post_id)
    if not isinstance(post_id, int):
        abort(400, description="ID must be a number", post_id=post_id)
    if post_id in blog:
        return post_id
    abort(404, description="ID does not exist in this blog")
@app.route("/")
def index():
    """
    User accessing the landing page of our site.
    He'll see a mock menu and all available posts are
    displayed.
    :return: the index page
    """
    print("A User landed on our page. He'll see the following blogs:")
    print(blog.get_all_posts())
    return render_template(
        "index.html", blog_name=blog.get_name(), posts=blog.get_all_posts()
    )


@app.route("/post/<int:post_id>")
def get(post_id):
    """
    Accepts a GET request to the /post address. Fetches the post
    with the provided post_id and display it for the user
    :param post_id:
    :return:
    """
    print(f"User performed a GET request on /post/{post_id}")
    post_id = check_received_post_id(post_id)
    post = blog.get_post(post_id)
    if post:
        return render_template(
            "one_post.html",
            blog_name=blog.get_name(),
            post=post)
    abort(404, description="ID not found", post_id=post_id)


@app.route("/delete/<int:post_id>", methods=["GET"])
def delete(post_id):
    """
    Removes the provided post_id from the cache and json file
    :param post_id:
    :return:
    """
    print(f"User performed a DELETE request with arg {post_id}")
    post_to_delete = check_received_post_id(post_id)
    try:
        result = blog.delete(post_to_delete)
    except InternalServerError as e:
        print(f"Could not delete post {post_to_delete} due to: {e}")
        abort(
            500,
            description="We encountered an internal problem. Try again later.",
            post_id=post_to_delete,
        )
    if result:
        print(f"Post  {post_to_delete} deleted")
        return render_template(
            "index.html", blog_name=blog.get_name(), posts=blog.get_all_posts()
        )
    abort(404, description=f"A wrong id was provided: {post_to_delete}")

@app.route('/like/<int:post_id>')
def like(post_id):
    print(f"User performed a LIKE request for post {post_id}")
    blog.like(post_id)
    return render_template(
        "index.html", blog_name=blog.get_name(), posts=blog.get_all_posts()
    )

@app.route("/update/<int:post_id>", methods=["GET", "POST"])
def update(post_id):
    """
    The sequence for this routeconsists of 2 parts: 1. The user performs a "GET" request
    to the address to update a post with the provided post_id. Upon this request
    the update.html is returned with the details (author, title etc) of that post
    already pre-filled

    When the user clicks on "update", a POST request is send to this route and in the body of
    the POST request, the updated title, author, content, image is received
    Next step is to store this information in the class and into the json file and the updated
    posts are displayed.
    :param post_id:
    :return:
    """
    # Fetch the blog posts from the JSON file
    post_id = check_received_post_id(post_id)
    post = blog.get_post(post_id)
    print(f"User performed a {request.method} request with arg {post_id}")
    if post is None:
        # Post not found
        return "Post not found", 404

    if request.method == "POST":
        id_to_update = post_id
        title = request.form.get("title")
        author = request.form.get("author")
        content = request.form.get("content")
        new_image = request.files.get("image", None)
        cur_image = request.form.get("current_image", None)
        if title == "" or author == "" or len(title) < 4 or len(author) < 3:
            abort(
                400,
                description="Title and/or author was not provided or was too short")
        upd_post = {
            "id": id_to_update,
            "title": title,
            "author": author,
            "content": content,
            "likes": 0,
        }
        if new_image:
            upd_post["image"] = new_image
        else:
            upd_post["image"] = cur_image
        blog.delete(id_to_update, keep_image=True)
        new_id = blog.set(upd_post)
        if new_id == id_to_update:
            print(f"Post with id: {id_to_update} updated")
        else:
            print(
                f"Post with id: {id_to_update} updated. Now stored under id {new_id}")
        return render_template(
            "index.html", blog_name=blog.get_name(), posts=blog.get_all_posts()
        )
    # Else, it's a GET request
    # So display the update.html page
    return render_template("update.html", blog_name=blog.get_name(), post=post)


@app.route("/add", methods=["GET", "POST"])
def add():
    """
    The sequence of /add is very similar as the /update. Also here the sequence consists
    of 2 parts:
    1. The user performs a "GET" request to the address to add a post.
    Upon this request the add.html is returned to the client's browser. Here the user
    can fulfill all the fields. Another way of adding a new post is directly from the index.html

    When the user clicks on "add", a POST request is send to this route and in the body of
    the POST request, the title, author, content, image are received
    Next step is to store this information in the class and into the json file and the updated
    list of posts are displayed.
    :return:
    """
    if request.method == "GET":
        return render_template("add.html")
    print(
        f"User performed an ADD request with title {
            request.form.get(
                'title',
                "Not provided")}")
    try:
        title = request.form["title"]
        author = request.form["author"]
        content = request.form.get("content", "The title says it all")
        image = request.files.get("image", None)
        if title == "" or author == "" or len(title) < 4 or len(author) < 3:
            abort(
                400,
                description="Title and/or author was not provided or was too short")
    except KeyError:
        print("User performed an add request but no title and/or author was provided")
        abort(404, description="No title/author received")
    new_post = {"title": title, "author": author, "content": content}
    if image:
        new_post["image"] = image
    # print(dir(image))
    new_id = blog.set(new_post)
    print(f"New Post with id: {new_id} added")
    posts = blog.get_all_posts()
    return render_template(
        "index.html",
        blog_name=blog.get_name(),
        posts=posts)


@app.errorhandler(400)
def bad_user_request400(error):
    """ Error handling """
    return render_template("error.html", code=400,
                           message=error.description), 400


@app.errorhandler(404)
def bad_user_request404(error):
    """ Error handling """
    return render_template("error.html", code=404,
                           message=error.description), 404


@app.errorhandler(405)
def bad_user_request405(error):
    """ Error handling """
    return render_template("error.html", code=405,
                           message=error.description), 405


@app.errorhandler(500)
def internal_server_error500(error):
    """ Error handling """
    return render_template("error.html", code=500,
                           message=error.description), 500


def main():
    """
    Create the blog with initial data and start the flask server
    :return:
    """
    print("==========================================================================")
    initial_blog_posts = [
        {
            "id": 1,
            "author": "Frank Rijkaard",
            "title": "My first goal",
            "content": "This was my first goal for Ajax-1.",
            "image": "",
        },
        {
            "id": 2,
            "author": "Marco van Basten",
            "title": "My best memory @AJAX",
            "content": "The jersey is simply amazing!",
            "image": "",
        },
    ]
    if len(blog.get_all_posts()) == 0:
        for initial_post in initial_blog_posts:
            try:
                stored_id = blog.set(initial_post)
            except InternalServerError as e:
                return render_template(
                    url_for("static" + "/error.html"), code=500, message=e
                )
            print("Stored initial post with id ", stored_id)
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()
