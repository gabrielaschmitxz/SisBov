"""
Serviço para gerenciamento de propriedades
"""
from src.services.database import get_connection
from psycopg2.extras import RealDictCursor

def create_property(name, owner_name, city, state, cpf_cnpj=None, address=None, area=None, 
                   natural_pasture_area=None, cultivated_pasture_area=None, notes=None):
    """Cria uma nova propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        INSERT INTO properties (name, owner_name, city, state, cpf_cnpj, address, area, natural_pasture_area, cultivated_pasture_area, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (name, owner_name, city, state, cpf_cnpj, address, area, natural_pasture_area, cultivated_pasture_area, notes or None))
    property_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return property_id

def get_all_properties():
    """Retorna todas as propriedades cadastradas"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM properties ORDER BY name")
    properties = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return properties

def get_property(property_id):
    """Retorna uma propriedade específica"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM properties WHERE id = %s", (property_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None

def update_property(property_id, name, owner_name, city, state, cpf_cnpj=None, address=None, area=None,
                   natural_pasture_area=None, cultivated_pasture_area=None, notes=None):
    """Atualiza os dados de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE properties 
        SET name = %s, owner_name = %s, city = %s, state = %s, cpf_cnpj = %s, address = %s, 
            area = %s, natural_pasture_area = %s, cultivated_pasture_area = %s, notes = %s
        WHERE id = %s
    """, (name, owner_name, city, state, cpf_cnpj, address, area, natural_pasture_area, cultivated_pasture_area, notes, property_id))
    conn.commit()
    cursor.close()
    conn.close()

def delete_property(property_id):
    """Remove uma propriedade e todos os dados relacionados"""
    conn = get_connection()
    cursor = conn.cursor()
    # Remove dados relacionados (CASCADE já faz isso, mas vamos garantir)
    cursor.execute("DELETE FROM animals WHERE property_id = %s", (property_id,))
    cursor.execute("DELETE FROM births WHERE property_id = %s", (property_id,))
    cursor.execute("DELETE FROM sales WHERE property_id = %s", (property_id,))
    cursor.execute("DELETE FROM purchases WHERE property_id = %s", (property_id,))
    cursor.execute("DELETE FROM deaths WHERE property_id = %s", (property_id,))
    cursor.execute("DELETE FROM health_procedures WHERE property_id = %s", (property_id,))
    cursor.execute("DELETE FROM gtas WHERE property_id = %s", (property_id,))
    # Remove a propriedade
    cursor.execute("DELETE FROM properties WHERE id = %s", (property_id,))
    conn.commit()
    cursor.close()
    conn.close()
