import psycopg2
from psycopg2 import sql


def connect_db():
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="2904",
        host="localhost",
        port="5432"
    )
    return conn


def create_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            email VARCHAR(100) UNIQUE
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS phones (
            id SERIAL PRIMARY KEY,
            client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
            phone_number VARCHAR(15)
        );
        """)
        conn.commit()


def add_client(conn, first_name, last_name, email, phones=None):
    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO clients (first_name, last_name, email) VALUES (%s, %s, %s) RETURNING id;
        """, (first_name, last_name, email))
        client_id = cur.fetchone()[0]

        if phones:
            for phone in phones:
                add_phone(conn, client_id, phone)

        conn.commit()
        return client_id


def add_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO phones (client_id, phone_number) VALUES (%s, %s);
        """, (client_id, phone))
        conn.commit()


def change_client(conn, client_id, first_name=None, last_name=None, email=None, phones=None):
    with conn.cursor() as cur:
        if first_name:
            cur.execute("UPDATE clients SET first_name = %s WHERE id = %s;", (first_name, client_id))
        if last_name:
            cur.execute("UPDATE clients SET last_name = %s WHERE id = %s;", (last_name, client_id))
        if email:
            cur.execute("UPDATE clients SET email = %s WHERE id = %s;", (email, client_id))

        if phones is not None:
            cur.execute("DELETE FROM phones WHERE client_id = %s;", (client_id,))
            for phone in phones:
                add_phone(conn, client_id, phone)

        conn.commit()


def delete_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute("""
        DELETE FROM phones WHERE client_id = %s AND phone_number = %s;
        """, (client_id, phone))
        conn.commit()


def delete_client(conn, client_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM clients WHERE id = %s;", (client_id,))
        conn.commit()


def find_client(conn, first_name=None, last_name=None, email=None, phone=None):
    with conn.cursor() as cur:
        query = """
        SELECT c.id, c.first_name, c.last_name, c.email, p.phone_number 
        FROM clients c 
        LEFT JOIN phones p ON c.id = p.client_id 
        WHERE TRUE
        """
        params = []

        if first_name:
            query += " AND c.first_name ILIKE %s"
            params.append(f'%{first_name}%')
        if last_name:
            query += " AND c.last_name ILIKE %s"
            params.append(f'%{last_name}%')
        if email:
            query += " AND c.email ILIKE %s"
            params.append(f'%{email}%')
        if phone:
            query += " AND p.phone_number ILIKE %s"
            params.append(f'%{phone}%')

        cur.execute(query, params)
        results = cur.fetchall()
        return results


if __name__ == "__main__":
    conn = connect_db()
    create_db(conn)

    client_id = add_client(conn, "Иван", "Иванов", "ivanov@example.com", phones=["123456789", "987654321"])

    print("Поиск клиента по имени:")
    print(find_client(conn, first_name="Иван"))

    change_client(conn, client_id, email="ivanov_new@example.com", phones=["111222333"])

    print("Поиск клиента после изменения:")
    print(find_client(conn, email="ivanov_new@example.com"))

    delete_phone(conn, client_id, "111222333")


    print("Поиск клиента после удаления телефона:")
    print(find_client(conn, email="ivanov_new@example.com"))

    delete_client(conn, client_id)

    print("Поиск клиента после удаления:")
    print(find_client(conn, email="ivanov_new@example.com"))

    conn.close()