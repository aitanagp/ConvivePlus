from fastapi import FastAPI

from app.routers import students, users, attitudes, classroom, records, academic_years

app = FastAPI(debug=True)
app.include_router(users.router)
app.include_router(students.router)
app.include_router(attitudes.router)
app.include_router(classroom.router)
app.include_router(records.router)
app.include_router(academic_years.router)

@app.get("/")
async def root():
    return {"message": "Welcome to my first FastAPI API"}