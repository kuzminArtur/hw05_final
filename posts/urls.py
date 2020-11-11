from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name='index'),
    path('group/<slug:slug>/', views.group_posts, name='group'),
    path('new/', views.PostCreate.as_view(), name='new_post'),
    path('<str:username>/<int:post_id>/', views.post_view, name='post'),
    path('<str:username>/<int:post_id>/edit/', views.PostEdit.as_view(),
         name='post_edit'),
    path("<username>/<int:post_id>/comment/", views.CommentCreate.as_view(),
         name="add_comment"),
    path("follow/", views.follow_index, name="follow_index"),
    path("<str:username>/follow/", views.profile_follow,
         name="profile_follow"),
    path("<str:username>/unfollow/", views.profile_unfollow,
         name="profile_unfollow"),
    path('<str:username>/', views.profile, name='profile'),
    # Просмотр записи

]
