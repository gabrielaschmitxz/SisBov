"""
Serviço para gerenciamento de outros animais (não bovinos)
"""
from src.services.database import get_connection
from psycopg2.extras import RealDictCursor

def create_other_animal_group(property_id, species, sex, quantity, classification=None):
    """Cria ou atualiza um grupo de outros animais"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Verifica se já existe um grupo com essas características
    cursor.execute("""
        SELECT id, quantity FROM other_animals 
        WHERE property_id = %s AND species = %s AND sex = %s
    """, (property_id, species, sex))
    
    existing = cursor.fetchone()
    
    if existing:
        # Atualiza a quantidade e classificação
        new_quantity = existing['quantity'] + quantity
        cursor.execute("""
            UPDATE other_animals 
            SET quantity = %s, classification = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_quantity, classification, existing['id']))
    else:
        # Cria novo grupo
        cursor.execute("""
            INSERT INTO other_animals (property_id, species, sex, quantity, classification)
            VALUES (%s, %s, %s, %s, %s)
        """, (property_id, species, sex, quantity, classification))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_other_animals_by_property(property_id):
    """Retorna todos os grupos de outros animais de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM other_animals 
        WHERE property_id = %s 
        ORDER BY species, sex
    """, (property_id,))
    animals = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return animals

def get_total_other_animals(property_id):
    """Retorna o total de outros animais de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT SUM(quantity) as total FROM other_animals 
        WHERE property_id = %s
    """, (property_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['total'] if result and result['total'] else 0

