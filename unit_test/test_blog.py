import pytest
import app

"""
Test cases:
1 New BlogPost
1.1 Create a new blog post, without existing json file
1.2 Create a blog post with existing json file
1.3 list the blog posts 
"""

@pytest.fixture
def client():
    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client

def test_homepage_displays_blog_posts(client):
    response = client.get("/")

    html = response.data.decode()
    print(html)
    assert response.status_code == 200
    assert "Ajax" in html
    assert "John" in html
    assert "Jane" in html