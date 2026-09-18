import psycopg2

import config


def main():
    conn = psycopg2.connect(config.DATABASE_URL)
    with open("db/schema.sql") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    conn.close()
    print("Database schema created successfully.")


if __name__ == "__main__":
    main()
