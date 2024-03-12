import sqlite3
from sqlite3 import Error
import json
from collections import defaultdict, deque

def main():
    database = r"D:\sqlite.db"
    # create a database connection
    conn = create_connection(database)
    if conn is None:
        print("Error! cannot create the database connection.")

    """create table"""
    # sql_create_data_table = """ CREATE TABLE IF NOT EXISTS data_table (
    #                                     key string PRIMARY KEY,
    #                                     value text 
    #                                 ); """
    # create_table(conn, sql_create_data_table)
    # print("Table created successfully!")

    """edit table"""
    # Sample data (replace with your actual defaultdict)
    data = defaultdict(list)
    data['key3'].append(1)
    data['key3'].append(2)
    data['key4'].append('A')

    # Prepare SQL statement with placeholders
    sql = """INSERT INTO data_table (key, value) VALUES (?, ?)"""

    # Iterate through defaultdict items
    for key, value in data.items():
        # Convert deque to JSON string for storage
        json_value = serialize_deque(value)
        cursor = conn.cursor()
        cursor.execute(sql, (key, json_value))
        conn.commit()
    # 怎麼寫整個df進DB, 然後怎麼快速把df刪掉 &重建 能趕快再次收值
    signal2db.to_sql(name='signal_realtime', con=conn, if_exists='append', index=False)

    print("Data exported to the SQLite database successfully!")

    """ output table"""
    with conn:
        select_all_from_data_table(conn)
    print("Data loaded from the SQLite database successfully!")

    # Close the connection
    conn.close()

# Function to convert deque to JSON string
def serialize_deque(deque_obj):
    return json.dumps(list(deque_obj))  # Convert deque to list before serialization

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def select_all_from_data_table(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM data_table")

    rows = cur.fetchall()

    for row in rows:
        print(row)

if __name__ == '__main__':
    main()