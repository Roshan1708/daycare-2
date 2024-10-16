import pymysql

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Roshan@1705',
        database='daycare',
        cursorclass=pymysql.cursors.DictCursor
    )