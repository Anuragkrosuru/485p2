"""Views, one for each Insta485 page."""
from insta485.views.index import show_index
from insta485.views.accounts import *
from insta485.views.posts import *
from insta485.views.users import *
from insta485.views.likes import update_likes
from insta485.views.followers import show_followers
from insta485.views.following import show_following, handle_following
from insta485.views.explore import explore
from insta485.views import comments
from insta485.views.newpost import create_or_delete_post as create_post

