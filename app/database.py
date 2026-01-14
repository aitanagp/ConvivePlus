from app.models import StudentDb, UserDb
import mariadb
import sys

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
                sql = "INSERT INTO USER (username, name, password) VALUES (?, ?, ?)"
                values = (user.username, user.name, user.password)
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


def get_user_by_username(username: str) -> UserDb | None:
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, username, password FROM USER WHERE username = ?"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            if result:
                return UserDb(id=result[0], name=result[1], username=result[2], password=result[3])
            return None            
            
def get_user_by_email(email: str) -> UserDb | None:
    # Asumimos que el email se guarda en el campo username
    return get_user_by_username(email)

def get_user_by_id(user_id: int) -> UserDb | None:
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, username, password FROM USER WHERE id = ?"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return UserDb(id=result[0], name=result[1], username=result[2], password=result[3])
            return None

def get_all_users_db() -> list[UserDb]:
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, username, password FROM USER"
            cursor.execute(sql)
            results = cursor.fetchall()
            # Convertimos cada tupla en un objeto UserDb
            return [
                UserDb(id=row[0], name=row[1], username=row[2], password=row[3])
                for row in results
            ]

def get_all_students_db():
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, surname, email, age, student_group FROM STUDENT"
            cursor.execute(sql)
            result = cursor.fetchall()
            return [
                {"id": r[0], "name": r[1], "surname": r[2], "email": r[3], "age": r[4], "student_group": r[5]}
                for r in result
                ]

def update_user_db(user_id: int, data: dict):
    new_name = data.get("name")
    new_username = data.get("email") # Asumiendo que usamos email como username

    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "UPDATE USER SET name = ?, username = ? WHERE id = ?"
            cursor.execute(sql, (new_name, new_username, user_id))
            conn.commit()

def delete_user_db(user_id: int):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "DELETE FROM USER WHERE id = ?"
            cursor.execute(sql, (user_id,))
            conn.commit()
            