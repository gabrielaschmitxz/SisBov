"""
Serviço para gerenciamento de procedimentos sanitários
"""
from src.services.database import get_connection
from psycopg2.extras import RealDictCursor

def register_health_procedure(property_id, procedure_type, vaccination_type, purpose_disease, product, 
                              application_date, category, sex, age_range, quantity, 
                              next_application_date=None, notes=None):
    """Registra um procedimento sanitário"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO health_procedures 
        (property_id, procedure_type, vaccination_type, purpose_disease, product, application_date, 
         category, sex, age_range, quantity, next_application_date, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (property_id, procedure_type, vaccination_type, purpose_disease, product, application_date,
          category, sex, age_range, quantity, next_application_date, notes))
    conn.commit()
    cursor.close()
    conn.close()

def get_health_procedures_by_property(property_id):
    """Retorna todos os procedimentos sanitários de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM health_procedures 
        WHERE property_id = %s 
        ORDER BY application_date DESC
    """, (property_id,))
    procedures = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return procedures

def get_upcoming_procedures(property_id):
    """Retorna procedimentos com próxima aplicação agendada"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM health_procedures 
        WHERE property_id = %s AND next_application_date IS NOT NULL
        ORDER BY next_application_date ASC
    """, (property_id,))
    procedures = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return procedures
