from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models import ScheduleOut, ScheduleCreate, ScheduleImportItem, StudentOut
from app.database import (
    get_schedules_db, insert_schedule_db, link_user_schedule_db, 
    delete_schedule_db, get_students_by_schedule_id_db, get_user_by_username
)
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/v1/schedules",
    tags=["schedules"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[ScheduleOut])
async def get_schedules(user_id: int = None, student_group: str = None, current_user=Depends(get_current_user)):
    schedules = get_schedules_db(user_id=user_id, student_group=student_group)
    return schedules

@router.post("/", response_model=ScheduleOut)
async def create_schedule(schedule: ScheduleCreate, current_user=Depends(get_current_user)):
    # Solo administradores o ROOT podrían crear horarios, pero para simplificar lo permitimos.
    schedule_id = insert_schedule_db(
        schedule.day_of_week, schedule.start_time, schedule.end_time,
        schedule.student_group, schedule.subject
    )
    link_user_schedule_db(schedule.user_id, schedule_id)
    return ScheduleOut(id=schedule_id, **schedule.dict())

@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int, current_user=Depends(get_current_user)):
    delete_schedule_db(schedule_id)
    return {"message": "Schedule deleted successfully"}

@router.post("/import/")
async def import_schedules(schedules: List[ScheduleImportItem], current_user=Depends(get_current_user)):
    count = 0
    for s in schedules:
        user = get_user_by_username(s.username)
        if user:
            sid = insert_schedule_db(
                s.day_of_week, s.start_time, s.end_time,
                s.student_group, s.subject
            )
            link_user_schedule_db(user['id'], sid)
            count += 1
    return {"message": f"{count} schedules imported successfully"}

@router.get("/{schedule_id}/students", response_model=List[StudentOut])
async def get_schedule_students(schedule_id: int, current_user=Depends(get_current_user)):
    students = get_students_by_schedule_id_db(schedule_id)
    return students
