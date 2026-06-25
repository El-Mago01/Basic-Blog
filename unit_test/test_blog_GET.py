import pytest
import app
import os


"""
Test cases:
1 New BlogPost
1.1 Create a new blog post, without existing json file
1.2 Create a blog post with existing json file
1.3 list the blog posts 
"""

@pytest.fixture
def test_init():
    initial_blog_posts = [
        {"id": 1, "author": "John Doe", "title": "First Post", "content": "This is my first post."},
        {"id": 2, "author": "Jane Doe", "title": "Second Post", "content": "This is another post."}
    ]
    json_data_file = 'data/We Love Ajax.json'
    if os.path.exists(json_data_file):
        os.remove(json_data_file)
    my_blog = app.Blog("We Love Ajax")
    my_blog.set(initial_blog_posts)

    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client, my_blog
        # print('The Test is over!')
def test_homepage_displays_blog_posts(test_init):
    client, my_blog = test_init
    response = client.get("/")
    html = response.data.decode()
    print(html)
    assert len(my_blog.get_all_posts()) == 2
    assert response.status_code == 200
    assert "Ajax" in html
    assert "John" in html
    assert "Jane" in html