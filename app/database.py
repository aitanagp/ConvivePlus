import mariadb

from app.models import UserDb


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
                  sql = "insert into users (name, username, password) values (?, ?, ?)"
                  values = (user.name, user.username, user.password)
                  cursor.execute(sql, values)
                  conn.commit()
                  return cursor.lastrowid
def get_user_by_username(username: str) -> UserDb | None:
      # TODO: terminar esta función
      return None

users: list[UserDb] = [UserDb(id=1, 
                              name="Alice", 
                              username="alice", 
                              password="$2b$12$xdKFg1TAfywlvynZJDFtLufbRxuPMUus2jtNvSRe.LONH3TnheIPm"),
                        UserDb(id=2, 
                              name="Bob", 
                              username="bob", 
                              password="$2b$12$6O8UlSzs640s9.4xQyoRk.Kv0tfKb5GCPlLY7bcQNdf7aBtx5LGOy")]