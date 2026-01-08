"""
Serviço para geração de relatórios
"""
from src.services.animal_service import get_animals_by_property, get_births_by_property, get_deaths_by_property
from src.services.movement_service import get_sales_by_property, get_purchases_by_property
from src.services.health_service import get_health_procedures_by_property
from src.services.gta_service import get_gtas_by_property
from src.services.other_animals_service import get_other_animals_by_property

def generate_herd_composition_report(property_id):
    """Gera relatório de composição do rebanho"""
    animals = get_animals_by_property(property_id)
    return {
        'type': 'Composição do Rebanho',
        'data': animals,
        'total': sum(a['quantity'] for a in animals)
    }

def generate_births_report(property_id, start_date=None, end_date=None):
    """Gera relatório de nascimentos"""
    births = get_births_by_property(property_id)
    
    if start_date:
        births = [b for b in births if b['date'] >= start_date]
    if end_date:
        births = [b for b in births if b['date'] <= end_date]
    
    return {
        'type': 'Nascimentos',
        'data': births,
        'total': sum(b['quantity'] for b in births)
    }

def generate_deaths_report(property_id, start_date=None, end_date=None):
    """Gera relatório de mortes"""
    deaths = get_deaths_by_property(property_id)
    
    if start_date:
        deaths = [d for d in deaths if d['date'] >= start_date]
    if end_date:
        deaths = [d for d in deaths if d['date'] <= end_date]
    
    return {
        'type': 'Mortes',
        'data': deaths,
        'total': sum(d['quantity'] for d in deaths)
    }

def generate_sales_report(property_id, start_date=None, end_date=None):
    """Gera relatório de vendas"""
    sales = get_sales_by_property(property_id)
    
    if start_date:
        sales = [s for s in sales if s['date'] >= start_date]
    if end_date:
        sales = [s for s in sales if s['date'] <= end_date]
    
    return {
        'type': 'Vendas',
        'data': sales,
        'total': sum(s['quantity'] for s in sales)
    }

def generate_purchases_report(property_id, start_date=None, end_date=None):
    """Gera relatório de compras"""
    purchases = get_purchases_by_property(property_id)
    
    if start_date:
        purchases = [p for p in purchases if p['date'] >= start_date]
    if end_date:
        purchases = [p for p in purchases if p['date'] <= end_date]
    
    return {
        'type': 'Compras',
        'data': purchases,
        'total': sum(p['quantity'] for p in purchases)
    }

def generate_health_report(property_id, start_date=None, end_date=None):
    """Gera relatório sanitário"""
    procedures = get_health_procedures_by_property(property_id)
    
    if start_date:
        procedures = [p for p in procedures if p['application_date'] >= start_date]
    if end_date:
        procedures = [p for p in procedures if p['application_date'] <= end_date]
    
    return {
        'type': 'Procedimentos Sanitários',
        'data': procedures,
        'total_procedures': len(procedures),
        'total_animals': sum(p['quantity'] for p in procedures)
    }

def generate_other_animals_report(property_id):
    """Gera relatório de outros animais"""
    animals = get_other_animals_by_property(property_id)
    return {
        'type': 'Outros Animais',
        'data': animals,
        'total': sum(a['quantity'] for a in animals)
    }

def generate_annual_report(property_id, year):
    """Gera relatório anual consolidado"""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    return {
        'year': year,
        'herd_composition': generate_herd_composition_report(property_id),
        'births': generate_births_report(property_id, start_date, end_date),
        'deaths': generate_deaths_report(property_id, start_date, end_date),
        'sales': generate_sales_report(property_id, start_date, end_date),
        'purchases': generate_purchases_report(property_id, start_date, end_date),
        'health': generate_health_report(property_id, start_date, end_date),
        'other_animals': generate_other_animals_report(property_id)
    }

