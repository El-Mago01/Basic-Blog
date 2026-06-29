import pytest
import app
import os

"""
Test cases:
1 update post
1.1 Insert 2 posts, update on the first post and check received html
1.2 Insert 2 posts, update on the first post and check update

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
    updated_post = {
        "author": "John Doe Jr.",
        "title": "First Post - have fun",
        "content": "This is my first post. - have fun",
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
        yield client, test_blog, updated_post
        # print('The Test is over!')


# 1.1 Insert 2 posts, update on the first post and check received html
def test_1_1_Insert_2_posts_update_on_the_first_post_and_check_received_html(test_init):
    client, test_blog, upd_post = test_init
    response_update1 = client.get("/update/1")
    html_upd1 = response_update1.data.decode()
    print(test_blog.get_all_posts())
    assert "Edit Blog Post" in html_upd1
    assert len(test_blog.get_all_posts()) == 2
    assert response_update1.status_code == 200


# 1.2 Insert 2 posts, update on the first post and check update
def test_1_2_Insert_2_posts_update_on_the_first_post_and_check_update(test_init):
    client, test_blog, upd_post = test_init
    response_update1 = client.get("/update/1")
    response_update2 = client.post("/update/1", data=upd_post)
    html_upd1 = response_update1.data.decode()
    html_upd2 = response_update2.data.decode()
    print(test_blog.get_all_posts())
    assert "Edit Blog Post" in html_upd1
    assert "John Doe Jr" in html_upd2
    assert "First Post - have fun" in html_upd2
    assert "This is my first post. - have fun" in html_upd2
    assert len(test_blog.get_all_posts()) == 2
    assert response_update1.status_code == 200
    assert response_update2.status_code == 200
    assert "<title>We Love Ajax</title>" in html_upd2
    assert "Jane" in html_upd2
    assert "Second Post" in html_upd2
    assert "ID: 2" in html_upd2
    assert "ID: 1" in html_upd2

def test_2_1_like_ID_1(test_init):
    client, test_blog, upd_post = test_init
    response_like = client.get("/like/1")
    response_like = client.get("/like/2")
    response_like = client.get("/like/2")
    assert "<span>1</span>" in response_like.data.decode()
    assert "<span>2</span>" in response_like.data.decode()
    assert "<span>0</span>" not in response_like.data.decode()
    assert "Like this post" in response_like.data.decode()

def test_2_2_like_ID_1_reset_after_update(test_init):
    client, test_blog, upd_post = test_init
    response_like = client.get("/like/1")
    response_like = client.get("/like/2")
    response_like = client.get("/like/2")
    assert "<span>2</span>" in response_like.data.decode()
    assert "<span>1</span>" in response_like.data.decode()
    response_update1 = client.get("/update/1")
    response_update2 = client.post("/update/1", data=upd_post)
    html_upd1 = response_update1.data.decode()
    html_upd2 = response_update2.data.decode()
    print(test_blog.get_all_posts())
    assert "<span>0</span>" in html_upd2
    assert "<span>2</span>" in html_upd2
    assert "<span>1</span>" not in html_upd2
    assert "Edit Blog Post" in html_upd1
    assert "John Doe Jr" in html_upd2
    assert "First Post - have fun" in html_upd2
    assert "This is my first post. - have fun" in html_upd2
    assert len(test_blog.get_all_posts()) == 2
    assert response_update1.status_code == 200
    assert response_update2.status_code == 200
    assert "<title>We Love Ajax</title>" in html_upd2
    assert "Jane" in html_upd2
    assert "Second Post" in html_upd2
    assert "ID: 2" in html_upd2
    assert "ID: 1" in html_upd2