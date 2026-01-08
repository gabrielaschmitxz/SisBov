"""
Serviço para gerenciamento de movimentações (vendas e compras)
"""
from src.services.database import get_connection
from src.services.animal_service import update_animal_quantity
from psycopg2.extras import RealDictCursor

def register_sale(property_id, date, category, sex, age_range, quantity, has_gta, gta_number=None, destination=None):
    """Registra uma venda e atualiza o rebanho"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Registra a venda
    cursor.execute("""
        INSERT INTO sales (property_id, date, category, sex, age_range, quantity, has_gta, gta_number, destination)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (property_id, date, category, sex, age_range, quantity, has_gta, gta_number, destination))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Atualiza o rebanho (reduz a quantidade)
    update_animal_quantity(property_id, "Corte", category, sex, -quantity)

def register_purchase(property_id, date, origin, category, sex, age_range, quantity, has_gta, gta_number=None):
    """Registra uma compra e atualiza o rebanho"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Registra a compra
    cursor.execute("""
        INSERT INTO purchases (property_id, date, origin, category, sex, age_range, quantity, has_gta, gta_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (property_id, date, origin, category, sex, age_range, quantity, has_gta, gta_number))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Atualiza o rebanho (aumenta a quantidade)
    update_animal_quantity(property_id, "Corte", category, sex, quantity)

def get_sales_by_property(property_id):
    """Retorna todas as vendas de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM sales 
        WHERE property_id = %s 
        ORDER BY date DESC
    """, (property_id,))
    sales = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return sales

def get_purchases_by_property(property_id):
    """Retorna todas as compras de uma propriedade"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM purchases 
        WHERE property_id = %s 
        ORDER BY date DESC
    """, (property_id,))
    purchases = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return purchases
