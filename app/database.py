from app.models import (
    StudentDb, UserDb, StudentUpdate, 
    ClassroomAssignmentIn, ClassroomTaskIn, AttendanceUpdate,
    DisciplinaryRecordOpen, DisciplinaryRecordStatusUpdate,
    AcademicYearIn
)
import mariadb
import sys
from datetime import date

# Configuración de la DB
db_config = {
    "host": "myapidb",
    "port": 3306,
    "user": "myapi",
    "password": "myapi",
    "database": "myapi",
}


def insert_user(user: UserDb) -> int:
    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO USER (username, name, password, role, department) VALUES (?, ?, ?, ?, ?)"
                values = (user.username, user.name, user.password, user.role, user.department)
                cursor.execute(sql, values)
                conn.commit()
                return cursor.lastrowid
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return -1

# Función extra para asignar rol (Profesor, Director, etc.)
def insert_user_role(user_id: int, role_table: str):
    """
    Inserta el ID del usuario en la tabla de rol correspondiente.
    role_table debe ser: 'TEACHER', 'DIRECTOR' o 'ROOT'
    """
    valid_tables = ['TEACHER', 'DIRECTOR', 'ROOT']
    if role_table not in valid_tables:
        return False

    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                sql = f"INSERT INTO {role_table} (user_id) VALUES (?)"
                cursor.execute(sql, (user_id,))
                conn.commit()
                return True
    except mariadb.Error as e:
        print(f"Error asignando rol: {e}")
        return False

def insert_student(student: StudentDb):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "INSERT INTO STUDENT (name, surname, email, age, student_group) VALUES (?, ?, ?, ?, ?)"
            values = (student.name, student.surname, student.email, student.age, student.student_group)
            cursor.execute(sql, values)
            conn.commit()
            return cursor.lastrowid

def get_student_id_by_email(email: str):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id FROM STUDENT WHERE email = ?"
            cursor.execute(sql, (email,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return None

def get_user_by_username(username: str) -> UserDb | None:
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, username, password, role, department FROM USER WHERE username = ?"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            if result:
                return UserDb(id=result[0], name=result[1], username=result[2], password=result[3], role=result[4], department=result[5])
            return None      
            
def get_user_by_email(email: str) -> UserDb | None:
    # Asumimos que el email se guarda en el campo username
    return get_user_by_username(email)

def get_user_by_id(user_id: int) -> UserDb | None:
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, username, password, role, department FROM USER WHERE id = ?"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return UserDb(id=result[0], name=result[1], username=result[2], password=result[3], role=result[4], department=result[5])
            return None

def get_all_users_db() -> list[UserDb]:
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, username, password, role, department FROM USER"
            cursor.execute(sql)
            results = cursor.fetchall()
            # Convertimos cada tupla en un objeto UserDb
            return [
                UserDb(id=row[0], name=row[1], username=row[2], password=row[3], role=row[4], department=row[5])
                for row in results
            ]

def get_all_students_db(student_group=None):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT s.id, s.name, s.surname, s.email, s.age, s.student_group, 
                       (SELECT COUNT(*) FROM PROBI_RECOGNITION WHERE student_id = s.id AND status = 'APPROVED') > 0 as is_probi
                FROM STUDENT s
            """
            params = []
            if student_group:
                sql += " WHERE s.student_group = ?"
                params.append(student_group)
                
            cursor.execute(sql, tuple(params))
            result = cursor.fetchall()
            return [
                {"id": r[0], "name": r[1], "surname": r[2], "email": r[3], "age": r[4], "student_group": r[5], "is_probi": bool(r[6])}
                for r in result
                ]

def update_user_db(user_id: int, data: dict):
    new_name = data.get("name")
    new_username = data.get("username")
    new_role = data.get("role")
    new_department = data.get("department")

    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "UPDATE USER SET name = ?, username = ?, role = ?, department = ? WHERE id = ?"
            cursor.execute(sql, (new_name, new_username, new_role, new_department, user_id))
            conn.commit()
            return True

def delete_user_db(user_id: int):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "DELETE FROM USER WHERE id = ?"
            cursor.execute(sql, (user_id,))
            conn.commit()

def insert_attitude(teacher_id: int, student_id: int, description: str, tipo: str):
    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                
                # Crear la Actitud base (ATTITUDE)
                # Ahora incluimos la fecha (created_at) aunque tenga default, por seguridad
                sql1 = "INSERT INTO ATTITUDE (description, status, created_at) VALUES (?, 'Active', ?)"
                cursor.execute(sql1, (description, date.today()))
                attitude_id = cursor.lastrowid # Guardamos el ID que se acaba de crear

                sql2 = "INSERT INTO LOG_ATTITUDE (user_id, attitude_id) VALUES (?, ?)"
                cursor.execute(sql2, (teacher_id, attitude_id))

                # Depende de si es Amonestación o Reconocimiento
                if tipo == "WARNING":
                    # Insertar en tabla WARNING
                    cursor.execute("INSERT INTO WARNING (attitude_id) VALUES (?)", (attitude_id,))
                    # Vincular al Alumno (STUDENT_WARNING)
                    cursor.execute("INSERT INTO STUDENT_WARNING (student_id, warning_id) VALUES (?, ?)", (student_id, attitude_id))
                
                elif tipo == "RECOGNITION":
                    # Insertar en tabla RECOGNITION
                    cursor.execute("INSERT INTO RECOGNITION (attitude_id) VALUES (?)", (attitude_id,))
                    # Vincular al Alumno (STUDENT_RECOGNITION)
                    cursor.execute("INSERT INTO STUDENT_RECOGNITION (student_id, recognition_id) VALUES (?, ?)", (student_id, attitude_id))

                # Guardar cambios
                conn.commit()
                return True

    except mariadb.Error as e:
        print(f"Error base de datos: {e}")
        return False
    
def insert_teacher_link(user_id: int):
    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO TEACHER (user_id) VALUES (?)"
                cursor.execute(sql, (user_id,))
                conn.commit()
                return True
    except mariadb.Error as e:
        print(f"Error al vincular profesor: {e}")
        return False
    
def insert_student_link(user_id: int):
    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO STUDENT (user_id) VALUES (?)"
                cursor.execute(sql, (user_id,))
                conn.commit()
                return True
    except mariadb.Error as e:
        print(f"Error al vincular estudiante: {e}")
        return False

# FUNCIONES PARA ACTITUDES

def get_attitudes_db(teacher_id=None):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT a.id, a.description, a.status, u.name as teacher_name, la.user_id
                FROM ATTITUDE a
                JOIN LOG_ATTITUDE la ON a.id = la.attitude_id
                JOIN USER u ON la.user_id = u.id
            """
            if teacher_id:
                sql += " WHERE la.user_id = ?"
                cursor.execute(sql, (teacher_id,))
            else:
                cursor.execute(sql)
            
            rows = cursor.fetchall()
            return [
                {"id": r[0], "description": r[1], "status": r[2], "teacher_name": r[3], "teacher_id": r[4]}
                for r in rows
            ]

def get_attitude_owner_id(attitude_id):
    """Para saber quién creó la actitud y si puede borrarla/editarla"""
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT user_id FROM LOG_ATTITUDE WHERE attitude_id = ?"
            cursor.execute(sql, (attitude_id,))
            result = cursor.fetchone()
            return result[0] if result else None

def update_attitude_db(attitude_id, description):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "UPDATE ATTITUDE SET description = ? WHERE id = ?"
            cursor.execute(sql, (description, attitude_id))
            conn.commit()
            return True

def delete_attitude_db(attitude_id):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            # Primero borramos de las tablas relacionadas
            sql = "DELETE FROM ATTITUDE WHERE id = ?"
            cursor.execute(sql, (attitude_id,))
            conn.commit()
            return True

# FUNCIONES PARA ALUMNOS

def get_student_by_id_db(student_id: int):
    # Busco al alumno por su ID
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, surname, email, age, student_group FROM STUDENT WHERE id = ?"
            cursor.execute(sql, (student_id,))
            r = cursor.fetchone()
            if r:
                cursor.execute("SELECT id FROM PROBI_RECOGNITION WHERE student_id = ? AND status = 'APPROVED'", (student_id,))
                is_probi = cursor.fetchone() is not None
                return {"id": r[0], "name": r[1], "surname": r[2], "email": r[3], "age": r[4], "student_group": r[5], "is_probi": is_probi}
            return None

def update_student_db(student_id: int, student_data: StudentUpdate):
    # Esto es para cambiar los datos del alumno
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            # Primero traigo lo que hay ahora por si acaso
            current = get_student_by_id_db(student_id)
            if not current:
                return False
            
            # Si el dato es None, me quedo con el que ya había
            name = student_data.name if student_data.name is not None else current["name"]
            surname = student_data.surname if student_data.surname is not None else current["surname"]
            email = student_data.email if student_data.email is not None else current["email"]
            age = student_data.age if student_data.age is not None else current["age"]
            student_group = student_data.student_group if student_data.student_group is not None else current["student_group"]

            sql = "UPDATE STUDENT SET name = ?, surname = ?, email = ?, age = ?, student_group = ? WHERE id = ?"
            cursor.execute(sql, (name, surname, email, age, student_group, student_id))
            conn.commit()
            return True

def delete_student_db(student_id: int):
    # Hay que borrar las actitudes para que no se queden huérfanas
    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                # Busco todas las actitudes de este alumno (amonestaciones y reconocimientos)
                sql_get_attitudes = """
                    SELECT warning_id FROM STUDENT_WARNING WHERE student_id = ?
                    UNION
                    SELECT recognition_id FROM STUDENT_RECOGNITION WHERE student_id = ?
                """
                cursor.execute(sql_get_attitudes, (student_id, student_id))
                attitude_ids = [row[0] for row in cursor.fetchall()]

                # Borro cada actitud de la tabla gorda ATTITUDE
                for aid in attitude_ids:
                    cursor.execute("DELETE FROM ATTITUDE WHERE id = ?", (aid,))
                
                # borro al alumno
                cursor.execute("DELETE FROM STUDENT WHERE id = ?", (student_id,))
                
                conn.commit()
                return True
    except mariadb.Error as e:
        print(f"Error borrando alumno: {e}")
        return False

# FUNCIONES PARA EL AULA DE CONVIVENCIA

def check_classroom_overlap(student_id: int, start_date, end_date, start_time, end_time):
    # Miro si el alumno ya tiene algo a esa misma hora y fecha
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT id FROM CLASSROOM_ASSIGNMENT
                WHERE student_id = ?
                AND (start_date <= ? AND end_date >= ?)
                AND (start_time < ? AND end_time > ?)
            """
            cursor.execute(sql, (student_id, end_date, start_date, end_time, start_time))
            return cursor.fetchone() is not None

def insert_classroom_assignment(assignment: ClassroomAssignmentIn, teacher_id: int):
    # Primero miro si se pisa con otro horario
    if check_classroom_overlap(assignment.student_id, assignment.start_date, assignment.end_date, assignment.start_time, assignment.end_time):
        return None
    
    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO CLASSROOM_ASSIGNMENT 
                    (student_id, teacher_id, start_date, end_date, start_time, end_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql, (assignment.student_id, teacher_id, assignment.start_date, assignment.end_date, assignment.start_time, assignment.end_time))
                conn.commit()
                return cursor.lastrowid
    except mariadb.Error as e:
        print(f"Error al asignar aula: {e}")
        return None

def get_daily_classroom_students(today, time_filter=None):
    # Saco los alumnos que tienen que estar hoy en el aula
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT ca.id, s.name, s.surname, ca.start_time, ca.end_time
                FROM CLASSROOM_ASSIGNMENT ca
                JOIN STUDENT s ON ca.student_id = s.id
                WHERE ca.start_date <= ? AND ca.end_date >= ?
            """
            params = [today, today]
            if time_filter:
                sql += " AND ca.start_time <= ? AND ca.end_time >= ?"
                params.extend([time_filter, time_filter])
            
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return [
                {"assignment_id": r[0], "name": r[1], "surname": r[2], "start_time": str(r[3]), "end_time": str(r[4])}
                for r in rows
            ]

def insert_classroom_task(task: ClassroomTaskIn):
    # Poner una tarea al alumno
    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO CLASSROOM_TASK (assignment_id, description) VALUES (?, ?)"
                cursor.execute(sql, (task.assignment_id, task.description))
                conn.commit()
                return cursor.lastrowid
    except mariadb.Error as e:
        print(f"Error al crear tarea: {e}")
        return None

def update_classroom_attendance(attendance: AttendanceUpdate):
    # Pasar lista
    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                # Miro si ya existe la fila de asistencia para ese día
                sql_check = "SELECT id FROM CLASSROOM_ATTENDANCE WHERE assignment_id = ? AND attendance_date = ?"
                cursor.execute(sql_check, (attendance.assignment_id, attendance.attendance_date))
                res = cursor.fetchone()
                
                if res:
                    sql = "UPDATE CLASSROOM_ATTENDANCE SET status = ? WHERE id = ?"
                    cursor.execute(sql, (attendance.status, res[0]))
                else:
                    sql = "INSERT INTO CLASSROOM_ATTENDANCE (assignment_id, attendance_date, status) VALUES (?, ?, ?)"
                    cursor.execute(sql, (attendance.assignment_id, attendance.attendance_date, attendance.status))
                
                conn.commit()
                return True
    except mariadb.Error as e:
        print(f"Error en asistencia: {e}")
        return False

def get_student_tasks_report(assignment_id: int):
    # Saco las tareas para el reporte
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT description, status FROM CLASSROOM_TASK WHERE assignment_id = ?"
            cursor.execute(sql, (assignment_id,))
            rows = cursor.fetchall()
            return [{"task": r[0], "status": r[1]} for r in rows]

# --- FUNCIONES PARA EXPEDIENTES DISCIPLINARIOS ---

def open_disciplinary_record_db(record_in: DisciplinaryRecordOpen):
    # 1. Mirar si todas las actitudes son WARNING
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            for aid in record_in.attitude_ids:
                cursor.execute("SELECT attitude_id FROM WARNING WHERE attitude_id = ?", (aid,))
                if not cursor.fetchone():
                    # Si alguna no es amonestación, no dejo abrir el expediente
                    return None
            
            # 2. Crear el expediente
            today = date.today()
            sql_record = "INSERT INTO DISCIPLINARY_RECORD (student_id, start_date, observations) VALUES (?, ?, ?)"
            cursor.execute(sql_record, (record_in.student_id, today, record_in.observations))
            record_id = cursor.lastrowid
            
            # 3. Vincular las actitudes
            for aid in record_in.attitude_ids:
                cursor.execute("INSERT INTO RECORD_ATTITUDE (record_id, attitude_id) VALUES (?, ?)", (record_id, aid))
            
            conn.commit()
            return record_id

def get_student_records_db(student_id: int):
    # Historial de un alumno
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, start_date, status, observations FROM DISCIPLINARY_RECORD WHERE student_id = ?"
            cursor.execute(sql, (student_id,))
            rows = cursor.fetchall()
            return [
                {"id": r[0], "start_date": str(r[1]), "status": r[2], "observations": r[3]}
                for r in rows
            ]

def update_record_status_db(record_id: int, update_data: DisciplinaryRecordStatusUpdate):
    # Cambiar el estado u observaciones
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            # Traigo lo que hay para no machacar si me pasan nulo
            cursor.execute("SELECT status, observations FROM DISCIPLINARY_RECORD WHERE id = ?", (record_id,))
            current = cursor.fetchone()
            if not current:
                return False
            
            new_status = update_data.status if update_data.status else current[0]
            new_obs = update_data.observations if update_data.observations is not None else current[1]
            
            sql = "UPDATE DISCIPLINARY_RECORD SET status = ?, observations = ? WHERE id = ?"
            cursor.execute(sql, (new_status, new_obs, record_id))
            conn.commit()
            return True

def get_pending_records_db():
    # Los que no estén cerrados
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT dr.id, s.name, s.surname, dr.start_date, dr.status
                FROM DISCIPLINARY_RECORD dr
                JOIN STUDENT s ON dr.student_id = s.id
                WHERE dr.status != 'Cerrado'
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [
                {"id": r[0], "student_name": f"{r[1]} {r[2]}", "start_date": str(r[3]), "status": r[4]}
                for r in rows
            ]

# --- FUNCIONES PARA CURSOS ACADÉMICOS ---

def insert_academic_year_db(year: AcademicYearIn):
    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO ACADEMIC_YEAR (start_year, end_year) VALUES (?, ?)"
                cursor.execute(sql, (year.start_year, year.end_year))
                conn.commit()
                return cursor.lastrowid
    except mariadb.Error as e:
        print(f"Error al crear curso: {e}")
        return None

def get_academic_years_db():
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, start_year, end_year, is_active FROM ACADEMIC_YEAR"
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [
                {"id": r[0], "start_year": r[1], "end_year": r[2], "is_active": bool(r[3])}
                for r in rows
            ]

def set_current_academic_year_db(year_id: int):
    try:
        with mariadb.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                # 1. Desactivar todos
                cursor.execute("UPDATE ACADEMIC_YEAR SET is_active = FALSE")
                # 2. Activar el seleccionado
                cursor.execute("UPDATE ACADEMIC_YEAR SET is_active = TRUE WHERE id = ?", (year_id,))
                
                if cursor.rowcount == 0:
                    conn.rollback()
                    return False
                
                conn.commit()
                return True
    except mariadb.Error as e:
        print(f"Error al activar curso: {e}")
        return False

# --- FUNCIONES PARA ESTADÍSTICAS ---

def get_stats_summary_db(start_date=None, end_date=None):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql_warnings = "SELECT COUNT(*) FROM WARNING w JOIN ATTITUDE a ON w.attitude_id = a.id"
            sql_recognitions = "SELECT COUNT(*) FROM RECOGNITION r JOIN ATTITUDE a ON r.attitude_id = a.id"
            
            params = []
            where_clauses = []
            if start_date:
                where_clauses.append("a.created_at >= ?")
                params.append(start_date)
            if end_date:
                where_clauses.append("a.created_at <= ?")
                params.append(end_date)
            
            if not start_date and not end_date:
                cursor.execute("SELECT start_year, end_year FROM ACADEMIC_YEAR WHERE is_active = TRUE")
                active_year = cursor.fetchone()
                if active_year:
                    where_clauses.append("a.created_at BETWEEN ? AND ?")
                    params.extend([f"{active_year[0]}-09-01", f"{active_year[1]}-08-31"])
            
            if where_clauses:
                where_str = " WHERE " + " AND ".join(where_clauses)
                sql_warnings += where_str
                sql_recognitions += where_str
            
            cursor.execute(sql_warnings, tuple(params))
            w_count = cursor.fetchone()[0]
            
            cursor.execute(sql_recognitions, tuple(params))
            r_count = cursor.fetchone()[0]
            
            return {"warnings": w_count, "recognitions": r_count, "total": w_count + r_count}

def get_stats_by_group_db(start_date=None, end_date=None):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT student_group, 
                       SUM(CASE WHEN tipo = 'WARNING' THEN 1 ELSE 0 END) as warnings,
                       SUM(CASE WHEN tipo = 'RECOGNITION' THEN 1 ELSE 0 END) as recognitions
                FROM (
                    SELECT s.student_group, 'WARNING' as tipo, a.created_at
                    FROM STUDENT s
                    JOIN STUDENT_WARNING sw ON s.id = sw.student_id
                    JOIN ATTITUDE a ON sw.warning_id = a.id
                    UNION ALL
                    SELECT s.student_group, 'RECOGNITION' as tipo, a.created_at
                    FROM STUDENT s
                    JOIN STUDENT_RECOGNITION sr ON s.id = sr.student_id
                    JOIN ATTITUDE a ON sr.recognition_id = a.id
                ) t
            """
            params = []
            where_clauses = []
            if start_date:
                where_clauses.append("created_at >= ?")
                params.append(start_date)
            if end_date:
                where_clauses.append("created_at <= ?")
                params.append(end_date)
            
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            
            sql += " GROUP BY student_group"
            
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return [
                {"student_group": r[0], "warnings": int(r[1]), "recognitions": int(r[2])}
                for r in rows
            ]

def get_top_students_stats_db(start_date=None, end_date=None, limit=10):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT s.id, s.name, s.surname, s.student_group, COUNT(sw.warning_id) as count
                FROM STUDENT s
                JOIN STUDENT_WARNING sw ON s.id = sw.student_id
                JOIN ATTITUDE a ON sw.warning_id = a.id
            """
            params = []
            where_clauses = []
            if start_date:
                where_clauses.append("a.created_at >= ?")
                params.append(start_date)
            if end_date:
                where_clauses.append("a.created_at <= ?")
                params.append(end_date)
            
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            
            sql += " GROUP BY s.id ORDER BY count DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return [
                {"student_id": r[0], "name": r[1], "surname": r[2], "student_group": r[3], "count": r[4]}
                for r in rows
            ]
# --- FUNCIONES PROBI ---

def init_probi_table():
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS PROBI_RECOGNITION (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                teacher_id INT NOT NULL,
                justification TEXT, status VARCHAR(20) DEFAULT 'PENDING',
                created_at DATE NOT NULL,
                FOREIGN KEY (student_id) REFERENCES STUDENT(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES USER(id) ON DELETE CASCADE
            )
            """
            cursor.execute(sql)
            conn.commit()

def insert_probi_nomination(student_id: int, teacher_id: int, justification: str):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "INSERT INTO PROBI_RECOGNITION (student_id, teacher_id, justification, created_at) VALUES (?, ?, ?, ?)"
            cursor.execute(sql, (student_id, teacher_id, justification, date.today()))
            conn.commit()
            return cursor.lastrowid

def get_probi_hall_of_fame():
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT p.id, s.name, s.surname, u.name as teacher_name, p.justification, p.created_at
                FROM PROBI_RECOGNITION p
                JOIN STUDENT s ON p.student_id = s.id
                JOIN USER u ON p.teacher_id = u.id
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [
                {"id": r[0], "student_name": f"{r[1]} {r[2]}", "teacher_name": r[3], "justification": r[4], "created_at": str(r[5])}
                for r in rows
            ]

def get_probi_suggestions():
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT s.id, s.name, s.surname, COUNT(sr.recognition_id) as rec_count
                FROM STUDENT s
                JOIN STUDENT_RECOGNITION sr ON s.id = sr.student_id
                WHERE s.id NOT IN (SELECT student_id FROM STUDENT_WARNING)
                GROUP BY s.id
                HAVING rec_count >= 1
                ORDER BY rec_count DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [
                {"student_id": r[0], "name": r[1], "surname": r[2], "recognitions": r[3]}
                for r in rows
            ]

def delete_probi_recognition(probi_id: int):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM PROBI_RECOGNITION WHERE id = ?", (probi_id,))
            conn.commit()
            return cursor.rowcount > 0
# --- HORARIOS ---
def get_schedules_db(user_id=None, student_group=None):
    with mariadb.connect(**db_config) as conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT s.id, s.day_of_week, s.start_time, s.end_time, s.student_group, s.subject FROM SCHEDULE s"
        params = []
        if user_id:
            query += " JOIN USER_SCHEDULE us ON s.id = us.schedule_id WHERE us.user_id = ?"
            params.append(user_id)
        elif student_group:
            query += " WHERE s.student_group = ?"
            params.append(student_group)
        
        cursor.execute(query, params)
        return cursor.fetchall()

def insert_schedule_db(day_of_week, start_time, end_time, student_group, subject):
    with mariadb.connect(**db_config) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO SCHEDULE (day_of_week, start_time, end_time, student_group, subject) VALUES (?, ?, ?, ?, ?)",
            (day_of_week, start_time, end_time, student_group, subject)
        )
        conn.commit()
        return cursor.lastrowid

def link_user_schedule_db(user_id, schedule_id):
    with mariadb.connect(**db_config) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO USER_SCHEDULE (user_id, schedule_id) VALUES (?, ?)",
            (user_id, schedule_id)
        )
        conn.commit()

def delete_schedule_db(schedule_id):
    with mariadb.connect(**db_config) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM SCHEDULE WHERE id = ?", (schedule_id,))
        conn.commit()

def get_students_by_schedule_id_db(schedule_id):
    with mariadb.connect(**db_config) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT student_group FROM SCHEDULE WHERE id = ?", (schedule_id,))
        sched = cursor.fetchone()
        if not sched:
            return []
        group = sched['student_group']
        cursor.execute("SELECT * FROM STUDENT WHERE student_group = ?", (group,))
        students = cursor.fetchall()
        for s in students:
            cursor.execute("SELECT 1 FROM LOG_ATTITUDE la JOIN ATTITUDE a ON la.attitude_id = a.id WHERE la.user_id = ? LIMIT 1", (s['id'],))
            s['is_probi'] = cursor.fetchone() is not None
        return students
