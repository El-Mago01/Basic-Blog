import pytest
import app
import os

"""
Test cases:
1 New BlogPost
1.1 Create a new blog post, without existing json file
1.2 Create a blog post with existing json file and add a new post
1.3 Create 3 blog posts with empty elements
1.4 Fault handling when json file can not be created
1.5 Fault handling when json file is not accessible
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
    json_data_file = "data/We Love Ajax.json"
    if os.path.exists(json_data_file):
        os.remove(json_data_file)
    test_blog = app.Blog("We Love Ajax")
    app.blog = test_blog  # This is needed to make the 'blog' variable in app to the test_blog here
    for test_post in initial_blog_posts:
        test_blog.set(test_post)
    app.app.config["TESTING"] = True
    with app.app.test_client() as client:
        yield client, test_blog
        # print('The Test is over!')


def test_1_1_create_blog_with_2_posts_1(test_init):
    client, test_blog = test_init
    response = client.get("/")
    html = response.data.decode()
    print(type(response))
    print(type(response.data))
    assert len(test_blog.get_all_posts()) == 2
    assert response.status_code == 200
    assert test_blog.get_name() == "We Love Ajax"
    assert "<title>We Love Ajax</title>" in html
    assert "John" in html
    assert "Jane" in html


def test_1_2_create_blog_with_2_posts_adding_1_extra(test_init):
    client, test_blog = test_init
    test_post = {
        "id": 1,
        "author": "Major Tom",
        "title": "Ajax has to buy more players",
        "content": "Can not wait for the players to start.",
    }
    test_blog.set(test_post)
    response = client.get("/")
    html = response.data.decode()
    assert len(test_blog.get_all_posts()) == 3
    assert response.status_code == 200
    assert len(test_blog.get_all_posts()) == 3
    print(test_blog.get_all_posts())
    assert "<title>We Love Ajax</title>" in html
    assert test_blog.get_free_id() == 4
    assert "Ajax has to buy more players" in html
    assert "Can not wait for the players to start." in html
    assert "John" in html
    assert "Jane" in html
    assert "Major Tom" in html
    assert "Second" in html


def test_1_3_create_blog_with_empty_elements(test_init):
    client, test_blog = test_init
    test_post = {
        "id": 1,
        "author": "Major Tom",
        "title": "",
        "content": "",
    }
    test_blog.set(test_post)
    response = client.get("/")
    html = response.data.decode()
    assert len(test_blog.get_all_posts()) == 3
    print(test_blog.get_all_posts())
    assert "Ajax" in html
    assert response.status_code == 200
    assert test_blog.get_free_id() == 4
    assert "Ajax" in html
    assert "Second" in html
    assert "Jane" in html
    assert "Major Tom" in html
