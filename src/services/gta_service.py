"""
Serviço para gerenciamento de GTAs (Guias de Trânsito Animal)
"""
from src.services.database import get_connection
from psycopg2.extras import RealDictCursor

def register_gta(property_id, movement_type, gta_number, emission_date, 
                 quantity, origin_destination, age_range=None, notes=None):
    """Registra uma GTA"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO gtas 
        (property_id, movement_type, gta_number, emission_date, quantity, origin_destination, age_range, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (property_id, movement_type, gta_number, emission_date, quantity, origin_destination, age_range, notes))
    conn.commit()
    cursor.close()
    conn.close()

def get_gtas_by_property(property_id):
    """Retorna todas as GTAs de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM gtas 
        WHERE property_id = %s 
        ORDER BY emission_date DESC
    """, (property_id,))
    gtas = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return gtas

def get_gta_by_number(property_id, gta_number):
    """Busca uma GTA pelo número"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM gtas 
        WHERE property_id = %s AND gta_number = %s
    """, (property_id, gta_number))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None
