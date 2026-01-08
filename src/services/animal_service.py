"""
Serviço para gerenciamento de animais
"""
from src.services.database import get_connection
from psycopg2.extras import RealDictCursor

def create_animal_group(property_id, purpose, category, sex, quantity, age_range=None, classification=None):
    """Cria ou atualiza um grupo de animais"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Verifica se já existe um grupo com essas características
    cursor.execute("""
        SELECT id, quantity FROM animals 
        WHERE property_id = %s AND purpose = %s AND category = %s AND sex = %s
    """, (property_id, purpose, category, sex))
    
    existing = cursor.fetchone()
    
    if existing:
        # Atualiza a quantidade, faixa etária e classificação
        new_quantity = existing['quantity'] + quantity
        cursor.execute("""
            UPDATE animals 
            SET quantity = %s, age_range = %s, classification = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_quantity, age_range, classification, existing['id']))
    else:
        # Cria novo grupo
        cursor.execute("""
            INSERT INTO animals (property_id, purpose, category, sex, quantity, age_range, classification)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (property_id, purpose, category, sex, quantity, age_range, classification))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_animals_by_property(property_id):
    """Retorna todos os grupos de animais de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM animals 
        WHERE property_id = %s 
        ORDER BY purpose, category, sex
    """, (property_id,))
    animals = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return animals

def get_total_animals(property_id):
    """Retorna o total de animais de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT SUM(quantity) as total FROM animals WHERE property_id = %s
    """, (property_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['total'] if result and result['total'] else 0

def update_animal_quantity(property_id, purpose, category, sex, quantity_change):
    """Atualiza a quantidade de animais (pode ser negativo para reduzir)"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT id, quantity FROM animals 
        WHERE property_id = %s AND purpose = %s AND category = %s AND sex = %s
    """, (property_id, purpose, category, sex))
    
    existing = cursor.fetchone()
    
    if existing:
        new_quantity = existing['quantity'] + quantity_change
        if new_quantity <= 0:
            # Remove o grupo se a quantidade ficar zero ou negativa
            cursor.execute("DELETE FROM animals WHERE id = %s", (existing['id'],))
        else:
            cursor.execute("""
                UPDATE animals 
                SET quantity = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_quantity, existing['id']))
    elif quantity_change > 0:
        # Cria novo grupo se não existir e a mudança for positiva
        cursor.execute("""
            INSERT INTO animals (property_id, purpose, category, sex, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (property_id, purpose, category, sex, quantity_change))
    
    conn.commit()
    cursor.close()
    conn.close()

def register_birth(property_id, date, sex, age_range, quantity, notes=None):
    """Registra um nascimento e atualiza o rebanho"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Registra o nascimento
    cursor.execute("""
        INSERT INTO births (property_id, date, sex, age_range, quantity, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (property_id, date, sex, age_range, quantity, notes))
    
    # Atualiza o rebanho (adiciona bezerros/bezerras)
    # Assumindo categoria "Bezerro(a)" para nascimentos
    category = "Bezerro" if sex == "Macho" else "Bezerra"
    purpose = "Corte"  # Pode ser ajustado conforme necessário
    
    cursor.execute("""
        SELECT id, quantity FROM animals 
        WHERE property_id = %s AND purpose = %s AND category = %s AND sex = %s
    """, (property_id, purpose, category, sex))
    
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE animals 
            SET quantity = quantity + %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (quantity, existing['id']))
    else:
        cursor.execute("""
            INSERT INTO animals (property_id, purpose, category, sex, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (property_id, purpose, category, sex, quantity))
    
    conn.commit()
    cursor.close()
    conn.close()

def register_death(property_id, date, category, sex, age_range, quantity, cause=None):
    """Registra uma morte e atualiza o rebanho"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Registra a morte
    cursor.execute("""
        INSERT INTO deaths (property_id, date, category, sex, age_range, quantity, cause)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (property_id, date, category, sex, age_range, quantity, cause))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Atualiza o rebanho (reduz a quantidade)
    update_animal_quantity(property_id, "Corte", category, sex, -quantity)

def get_births_by_property(property_id):
    """Retorna todos os nascimentos de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM births 
        WHERE property_id = %s 
        ORDER BY date DESC
    """, (property_id,))
    births = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return births

def get_deaths_by_property(property_id):
    """Retorna todas as mortes de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM deaths 
        WHERE property_id = %s 
        ORDER BY date DESC
    """, (property_id,))
    deaths = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return deaths
