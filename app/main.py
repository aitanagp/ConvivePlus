from fastapi import FastAPI

from app.routers import students, users, attitudes

app = FastAPI(debug=True)
app.include_router(users.router)
app.include_router(students.router)
app.include_router(attitudes.router)

@app.get("/")
async def root():
    return {"message": "Welcome to my first FastAPI API"}