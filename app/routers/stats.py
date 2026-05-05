from fastapi import APIRouter, status, HTTPException, Depends, Query
from typing import List, Optional
from datetime import date

from app.models import StatsSummary, GroupStats, TopStudentStats, UserDb
from app.database import (
    get_stats_summary_db,
    get_stats_by_group_db,
    get_top_students_stats_db
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/v1/stats", tags=["Statistics"])

# FUNCIÓN DE AYUDA PARA VERIFICAR ROLES
def check_stats_permissions(user: UserDb):
    if user.role not in ['ROOT', 'DIRECTOR']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Solo el Administrador o Dirección pueden ver las estadísticas"
        )

# RESUMEN GLOBAL
@router.get("/summary", response_model=StatsSummary)
async def get_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: UserDb = Depends(get_current_user)
):
    check_stats_permissions(current_user)
    return get_stats_summary_db(start_date, end_date)

# DESGLOSE POR GRUPOS
@router.get("/by-group", response_model=List[GroupStats])
async def get_by_group(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: UserDb = Depends(get_current_user)
):
    check_stats_permissions(current_user)
    return get_stats_by_group_db(start_date, end_date)

# TOP ALUMNOS CON INCIDENCIAS
@router.get("/top-students", response_model=List[TopStudentStats])
async def get_top_students(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: UserDb = Depends(get_current_user)
):
    check_stats_permissions(current_user)
    return get_top_students_stats_db(start_date, end_date, limit)
