from app.models import StudentDb, UserDb
import mariadb
import sys

db_config = {
    "host": "myapidb",
    "port": 3306,
    "user": "myapi",
    "password": "myapi",
    "database": "myapi",
}

def insert_user(user: UserDb):
    with mariadb.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            sql = "INSERT INTO USER (username, name, password) VALUES (?, ?, ?)"
            values = (user.username, user.name, user.password)
            cursor.execute(sql, values)
            conn.commit()
            return cursor.lastrowid

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