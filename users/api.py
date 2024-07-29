from datetime import date
from typing import Optional
from ninja import NinjaAPI, Schema
from django.shortcuts import get_object_or_404
from .models import User
import requests
from django.utils import timezone
from datetime import datetime

api = NinjaAPI()

class UserSchema(Schema):
    id: int
    email: str
    first_name: str
    last_name: str
    avatar: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

@api.get("/user/fetch")
def fetch_users(request, page: Optional[int] = None):
    if not page:
        return {"error": "Missing query parameter 'page'"}
    url = f"https://reqres.in/api/users?page={page}"
    response = requests.get(url)
    data = response.json()
    fetched_users = []
    for user_data in data['data']:
        if not User.objects.filter(id=user_data['id']).exists():
            user = User.objects.create(
                id=user_data['id'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                avatar=user_data['avatar']
            )
            fetched_users.append(UserSchema.from_orm(user))
    return fetched_users

@api.get("/user/{user_id}", response=UserSchema)
def get_user(request, user_id: int):
    user = get_object_or_404(User, id=user_id, deleted_at__isnull=True)
    print(user.deleted_at)
    if user.deleted_at:
        return {"error": "User not found"}, 404
    return user

@api.get("/user", response=UserSchema)
def list_users(request):
    users = User.objects.filter(deleted_at__isnull=True)
    return users

class UserCreateSchema(Schema):
    email: str
    first_name: str
    last_name: str
    avatar: str

@api.post("/user", response=UserSchema)
def create_user(request, payload: UserCreateSchema):
    user = User.objects.create(**payload.dict())
    return user

@api.put("/user/{user_id}", response=UserSchema)
def update_user(request, user_id: int, payload: UserCreateSchema):
    user = get_object_or_404(User, id=user_id, deleted_at__isnull=True)
    for attr, value in payload.dict().items():
        setattr(user, attr, value)
    user.updated_at = timezone.now()
    user.save()
    return user

@api.delete("/user/{user_id}")
def delete_user(request, user_id: int):
    authorization_header = request.headers.get('Authorization')
    if authorization_header != '3cdcnTiBsl':
        return {"error": "Unauthorized"}, 401
    user = get_object_or_404(User, id=user_id, deleted_at__isnull=True)
    user.deleted_at = timezone.now()
    user.save()
    return {"success": True}
