from django.contrib import admin
from django.urls import path
from  .views import RegisterView,LoginView,UserView,LogoutView,TodoView

urlpatterns = [
   path('signup',RegisterView.as_view()),
   path('login',LoginView.as_view()),
   path('user',UserView.as_view()),
   path('logout',LogoutView.as_view()),
   path('todos',TodoView.as_view(), name='todos'),
   path('todos/delete_todo/<int:id>/', TodoView.as_view(), name='delete_todo_by_id'),
   path('todos/delete_all_todos',TodoView.as_view(), name='delete_all_todos'),
   path('todos/<int:id>',TodoView.as_view(), name='todo-delete'),
]
