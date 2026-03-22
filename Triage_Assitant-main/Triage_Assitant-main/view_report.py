from db import get_db_connection

def view(search=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search:
        query = """
        SELECT * FROM reports 
        WHERE patient_name LIKE %s OR patient_id LIKE %s
        ORDER BY created_at DESC
        """
        like_search = f"%{search}%"
        cursor.execute(query, (like_search, like_search))
    else:
        query = "SELECT * FROM reports ORDER BY created_at DESC"
        cursor.execute(query)

    reports = cursor.fetchall()

    cursor.close()
    conn.close()

    return reports