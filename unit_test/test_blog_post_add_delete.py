import pytest
import app
import os

"""
Test cases:
1 add and delete BlogPost
1.1 Insert 3 posts, delete the first post
1.2 Add 2 posts. Delete the last post
1.3 Add 2 posts. Delete post with id-1, add a new post
1.4 Call delete with a non existing post-id
1.5 Call delete with an wrong type for post-id 
"""


@pytest.fixture
def test_init():
    initial_blog_posts = [
        {
            "id": 1,
            "author": "John Doe",
            "title": "First Post",
            "content": "This is my first post.",
        },
        {
            "id": 2,
            "author": "Jane Doe",
            "title": "Second Post",
            "content": "This is another post.",
        },
    ]
    a_post = {
        "author": "Major Tom",
        "title": "Ajax has to buy more players",
        "content": "Can not wait for the players to start.",
    }
    json_data_file = "data/We Love Ajax.json"
    if os.path.exists(json_data_file):
        os.remove(json_data_file)
    test_blog = app.Blog("We Love Ajax")
    app.blog = test_blog  # This is needed to link the 'blog' variable in app.py to the test_blog here
    for test_post in initial_blog_posts:
        an_id = test_blog.set(test_post)
        print("Stored blog with id : ", an_id)
    app.app.config["TESTING"] = True
    with app.app.test_client() as client:
        yield client, test_blog, a_post
        # print('The Test is over!')


# 1.1 Insert 3 posts, delete the first post


def test_1_1_Insert_3_posts_delete_the_first_post(test_init):
    client, test_blog, test_post = test_init
    response_add = client.post("/add", data=test_post)
    response_del = client.get("/delete/1")
    html = response_del.data.decode()
    print(test_blog.get_all_posts())
    assert test_blog.get_free_id() == 1
    assert "John" not in html
    assert len(test_blog.get_all_posts()) == 2
    assert response_del.status_code == 200
    assert response_add.status_code == 200
    assert test_blog.get_name() == "We Love Ajax"
    assert "<title>We Love Ajax</title>" in html
    assert "Jane" in html
    assert "First Post" not in html
    assert "Second Post" in html
    assert "ID: 2" in html
    assert "ID: 1" not in html
    assert "ID: 3" in html


# 1.2 Add 2 posts. Delete the last post
def test_1_2_Add_2_posts_Delete_the_last_post(test_init):
    client, test_blog, test_post = test_init
    response = client.get("/delete/2")
    html = response.data.decode()
    print(test_blog.get_all_posts())
    assert test_blog.get_free_id() == 2
    assert "John" in html
    assert len(test_blog.get_all_posts()) == 1
    assert response.status_code == 200
    assert test_blog.get_name() == "We Love Ajax"
    assert "<title>We Love Ajax</title>" in html
    assert "Jane" not in html
    assert "First Post" in html
    assert "Second Post" not in html
    assert "ID: 2" not in html
    assert "ID: 1" in html


# 1.3 Add 2 posts. Delete post with id-1, add a new post
def test_1_3_Add_2_posts_Delete_post_with_id_1_add_a_new_post(test_init):
    client, test_blog, test_post = test_init
    response_del = client.get("/delete/1")
    html_del = response_del.data.decode()
    response_add = client.post("/add", data=test_post)
    html_add = response_add.data.decode()
    assert len(test_blog.get_all_posts()) == 2
    assert response_del.status_code == 200
    assert response_add.status_code == 200
    print(test_blog.get_all_posts())
    assert "<title>We Love Ajax</title>" in html_add
    assert test_blog.get_free_id() == 3
    assert "Ajax has to buy more players" in html_add
    assert "Can not wait for the players to start." in html_add
    assert "John" not in html_del
    assert "Jane" in html_add
    assert "Major Tom" in html_add
    assert "Second" in html_add
    assert "ID: 2" in html_add
    assert "ID: 1" in html_add
    assert "ID: 3" not in html_add


# 1.4 Call delete with a non existing post_id
def test_1_4_Call_delete_with_a_non_existing_post_id(test_init):
    client, test_blog, test_post = test_init
    response_add = client.post("/add", data=test_post)
    html_add = response_add.data.decode()
    response_del = client.get("/delete/4")
    html_del = response_del.data.decode()
    assert len(test_blog.get_all_posts()) == 3
    assert response_del.status_code == 404  # Not Found
    assert response_add.status_code == 200
    print(test_blog.get_all_posts())
    assert "404 - A wrong id was provided: 4" in html_del
    assert test_blog.get_free_id() == 4
    assert "Ajax has to buy more players" in html_add
    assert "ID: 3" in html_add
    assert "Can not wait for the players to start." in html_add
    assert "John" in html_add
    assert "Jane" in html_add
    assert "Major Tom" in html_add
    assert "Second" in html_add
    assert "First" in html_add


# 1.5 Call delete with a wrong type for post-id
def test_1_4_Call_delete_with_an_wrong_type_for_postid(test_init):
    client, test_blog, test_post = test_init
    response_add = client.post("/add", data=test_post)
    html_add = response_add.data.decode()
    response_del = client.get("/delete/k4")
    html_del = response_del.data.decode()
    assert len(test_blog.get_all_posts()) == 3
    assert response_del.status_code == 404  # Not Found
    assert response_add.status_code == 200
    print(test_blog.get_all_posts())
    assert "404 - The requested URL was not found on the server." in html_del
    assert test_blog.get_free_id() == 4
    assert "Ajax has to buy more players" in html_add
    assert "ID: 3" in html_add
    assert "Can not wait for the players to start." in html_add
    assert "John" in html_add
    assert "Jane" in html_add
    assert "Major Tom" in html_add
    assert "Second" in html_add
    assert "First" in html_add
