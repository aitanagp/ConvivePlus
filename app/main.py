from fastapi import FastAPI

from app.routers import students, users

app = FastAPI(debug=True)
app.include_router(users.router)
app.include_router(students.router)

@app.get("/")
async def root():
    return {"message": "Welcome to my first FastAPI API"}