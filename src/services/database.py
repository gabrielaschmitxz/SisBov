"""
Serviço de gerenciamento do banco de dados PostgreSQL
"""
import psycopg2
import os
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# String de conexão do PostgreSQL (Neon)
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://neondb_owner:npg_Tf1IpyPm0QFk@ep-broad-sun-ahovkkf5-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
)

def get_connection():
    """Retorna uma conexão com o banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        return conn
    except psycopg2.OperationalError as e:
        raise ConnectionError(f"Erro ao conectar ao banco de dados: {str(e)}")
    except Exception as e:
        raise ConnectionError(f"Erro inesperado ao conectar ao banco: {str(e)}")

def init_database():
    """Inicializa o banco de dados criando todas as tabelas necessárias"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Tabela de propriedades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                owner_name VARCHAR(255) NOT NULL,
                cpf_cnpj VARCHAR(20),
                address TEXT,
                city VARCHAR(255) NOT NULL,
                state VARCHAR(255) NOT NULL,
                area DECIMAL(10, 2),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Adicionar novos campos se a tabela já existir (migração)
        try:
            cursor.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS cpf_cnpj VARCHAR(20)")
            cursor.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS address TEXT")
            cursor.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS natural_pasture_area DECIMAL(10, 2)")
            cursor.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS cultivated_pasture_area DECIMAL(10, 2)")
        except:
            pass  # Campos já existem ou erro na migração
        
        # Tabela de animais (cadastro por grupo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS animals (
                id SERIAL PRIMARY KEY,
                property_id INTEGER NOT NULL,
                purpose VARCHAR(50) NOT NULL,
                category VARCHAR(50) NOT NULL,
                sex VARCHAR(50) NOT NULL,
                quantity INTEGER NOT NULL,
                classification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)
        
        # Adicionar campos se a tabela já existir
        try:
            cursor.execute("ALTER TABLE animals ADD COLUMN IF NOT EXISTS classification TEXT")
            cursor.execute("ALTER TABLE animals ADD COLUMN IF NOT EXISTS age_range VARCHAR(50)")
        except:
            pass
        
        # Tabela de nascimentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS births (
                id SERIAL PRIMARY KEY,
                property_id INTEGER NOT NULL,
                date DATE NOT NULL,
                sex VARCHAR(50) NOT NULL,
                age_range VARCHAR(50),
                quantity INTEGER NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)
        
        # Adicionar campo de faixa etária se a tabela já existir
        try:
            cursor.execute("ALTER TABLE births ADD COLUMN IF NOT EXISTS age_range VARCHAR(50)")
        except:
            pass
        
        # Tabela de vendas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                property_id INTEGER NOT NULL,
                date DATE NOT NULL,
                category VARCHAR(50) NOT NULL,
                sex VARCHAR(50) NOT NULL,
                age_range VARCHAR(50),
                quantity INTEGER NOT NULL,
                has_gta BOOLEAN DEFAULT FALSE,
                gta_number VARCHAR(255),
                destination VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)
        
        # Adicionar campo de faixa etária se a tabela já existir
        try:
            cursor.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS age_range VARCHAR(50)")
        except:
            pass
        
        # Tabela de compras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY,
                property_id INTEGER NOT NULL,
                date DATE NOT NULL,
                origin VARCHAR(255) NOT NULL,
                category VARCHAR(50) NOT NULL,
                sex VARCHAR(50) NOT NULL,
                age_range VARCHAR(50),
                quantity INTEGER NOT NULL,
                has_gta BOOLEAN DEFAULT FALSE,
                gta_number VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)
        
        # Adicionar campo de faixa etária se a tabela já existir
        try:
            cursor.execute("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS age_range VARCHAR(50)")
        except:
            pass
        
        # Tabela de mortes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deaths (
                id SERIAL PRIMARY KEY,
                property_id INTEGER NOT NULL,
                date DATE NOT NULL,
                category VARCHAR(50) NOT NULL,
                sex VARCHAR(50) NOT NULL,
                age_range VARCHAR(50),
                quantity INTEGER NOT NULL,
                cause TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)
        
        # Adicionar campo de faixa etária se a tabela já existir
        try:
            cursor.execute("ALTER TABLE deaths ADD COLUMN IF NOT EXISTS age_range VARCHAR(50)")
        except:
            pass
        
        # Tabela de procedimentos sanitários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_procedures (
                id SERIAL PRIMARY KEY,
                property_id INTEGER NOT NULL,
                procedure_type VARCHAR(100) NOT NULL,
                vaccination_type VARCHAR(50),
                purpose_disease VARCHAR(255) NOT NULL,
                product VARCHAR(255) NOT NULL,
                application_date DATE NOT NULL,
                category VARCHAR(50) NOT NULL,
                sex VARCHAR(50) NOT NULL,
                age_range VARCHAR(50),
                quantity INTEGER NOT NULL,
                next_application_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)
        
        # Adicionar campos se a tabela já existir
        try:
            cursor.execute("ALTER TABLE health_procedures ADD COLUMN IF NOT EXISTS age_range VARCHAR(50)")
            cursor.execute("ALTER TABLE health_procedures ADD COLUMN IF NOT EXISTS vaccination_type VARCHAR(50)")
        except:
            pass
        
        # Tabela de GTAs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gtas (
                id SERIAL PRIMARY KEY,
                property_id INTEGER NOT NULL,
                movement_type VARCHAR(100) NOT NULL,
                gta_number VARCHAR(255) NOT NULL,
                emission_date DATE NOT NULL,
                quantity INTEGER NOT NULL,
                origin_destination VARCHAR(255) NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)
        
        # Tabela de outros animais (não bovinos)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS other_animals (
                id SERIAL PRIMARY KEY,
                property_id INTEGER NOT NULL,
                species VARCHAR(50) NOT NULL,
                sex VARCHAR(50) NOT NULL,
                quantity INTEGER NOT NULL,
                classification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)
        
        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Criar usuários padrão se não existirem
        try:
            # Importar aqui para evitar dependência circular
            from src.services.user_service import UserService
            UserService.ensure_default_users()
        except Exception as e:
            print(f"Erro ao criar usuarios padrao: {e}")
            pass  # Ignora se usuário já existe
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
