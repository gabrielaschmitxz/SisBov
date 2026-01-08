"""
Serviço unificado de gerenciamento de usuários
"""
import hashlib
from src.services.database import get_connection
from psycopg2.extras import RealDictCursor


class UserService:
    """Classe para gerenciar todas as operações de usuário"""
    
    @staticmethod
    def hash_password(password):
        """Gera hash da senha usando SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def create_user(username, password, name):
        """Cria um novo usuário"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            hashed_password = UserService.hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, name)
                VALUES (%s, %s, %s)
                RETURNING id, username, name
            """, (username, hashed_password, name))
            user = cursor.fetchone()
            conn.commit()
            return dict(user) if user else None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def authenticate_user(username, password):
        """Autentica um usuário"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            hashed_password = UserService.hash_password(password)
            cursor.execute("""
                SELECT id, username, name FROM users
                WHERE username = %s AND password_hash = %s
            """, (username, hashed_password))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_user_by_id(user_id):
        """Obtém dados de um usuário por ID"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT id, username, name FROM users
                WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_user_by_username(username):
        """Obtém dados de um usuário por username"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT id, username, name FROM users
                WHERE username = %s
            """, (username,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def user_exists(username):
        """Verifica se um usuário existe"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            count = result[0] if isinstance(result, tuple) else result['count']
            return count > 0
        except Exception as e:
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update_password(user_id, old_password, new_password):
        """Atualiza a senha do usuário"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Verifica senha antiga
            old_hashed = UserService.hash_password(old_password)
            cursor.execute("""
                SELECT id FROM users
                WHERE id = %s AND password_hash = %s
            """, (user_id, old_hashed))
            if not cursor.fetchone():
                return False
            
            # Atualiza senha
            new_hashed = UserService.hash_password(new_password)
            cursor.execute("""
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
            """, (new_hashed, user_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update_name(user_id, name):
        """Atualiza o nome do usuário"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                UPDATE users
                SET name = %s
                WHERE id = %s
                RETURNING id, username, name
            """, (name, user_id))
            user = cursor.fetchone()
            conn.commit()
            return dict(user) if user else None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def ensure_default_users():
        """Garante que os usuários padrão existam no banco"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Definir usuários padrão
            default_users = [
                {
                    'username': 'luiz',
                    'password': 'luiz123',
                    'name': 'Luiz de Lima Pereira'
                },
                {
                    'username': 'admin',
                    'password': 'admin123',
                    'name': 'Administrador'
                }
            ]
            
            for user_data in default_users:
                # Verificar se usuário existe
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (user_data['username'],))
                result = cursor.fetchone()
                count = result[0] if isinstance(result, tuple) else result.get('count', result[0])
                
                if count == 0:
                    # Criar usuário
                    hashed_password = UserService.hash_password(user_data['password'])
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, name)
                        VALUES (%s, %s, %s)
                    """, (user_data['username'], hashed_password, user_data['name']))
                    print(f"Usuario '{user_data['username']}' criado com sucesso")
                else:
                    # Atualizar nome se usuário já existir (para garantir nome correto)
                    cursor.execute("""
                        UPDATE users 
                        SET name = %s
                        WHERE username = %s
                    """, (user_data['name'], user_data['username']))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Erro ao criar usuarios padrao: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()


# Funções de compatibilidade (para não quebrar código existente)
def hash_password(password):
    """Função de compatibilidade"""
    return UserService.hash_password(password)


def create_user(username, password, name):
    """Função de compatibilidade"""
    return UserService.create_user(username, password, name)


def authenticate_user(username, password):
    """Função de compatibilidade"""
    return UserService.authenticate_user(username, password)


def get_user(user_id):
    """Função de compatibilidade - obtém usuário por ID"""
    return UserService.get_user_by_id(user_id)


def update_password(user_id, old_password, new_password):
    """Função de compatibilidade"""
    return UserService.update_password(user_id, old_password, new_password)

