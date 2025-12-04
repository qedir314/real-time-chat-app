from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError

from models.user import User
from auth.core import get_password_hash, verify_password, create_access_token, get_user_from_token
from config.database import users_collection

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup")
async def signup(user: User):
    hashed_password = get_password_hash(user.password)
    user_dict = user.model_dump()
    user_dict.pop("password")  # Remove plain password
    user_dict["hashed_password"] = hashed_password
    try:
        users_collection.insert_one(user_dict)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or Username already registered",
        )
    return {"message": "User created successfully"}


@router.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request})


@router.post("/signin")
async def signin(form_data: OAuth2PasswordRequestForm = Depends()):
    # Try to find user by email OR username
    user = users_collection.find_one({
        "$or": [
            {"email": form_data.username},
            {"username": form_data.username}
        ]
    })

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["email"]})
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )
    return response


@router.get("/me")
async def me(request: Request):
    token = request.cookies.get("access_token")
    if token:
        user = await get_user_from_token(token.split(" ")[1])
        if user:
            return user
    raise HTTPException(status_code=401, detail="Not authenticated")
