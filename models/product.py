from mysql.connector import Error  # Add this import at the top
from db.database_config import create_connection

class Product:
    @staticmethod
    def get_products_by_ligne():
        conn = create_connection()
        products_by_ligne = {}
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT DISTINCT ligne FROM products")
                lignes = [row['ligne'] for row in cursor.fetchall()]
                
                for ligne in lignes:
                    cursor.execute("SELECT name, cycle_time FROM products WHERE ligne = %s", (ligne,))
                    products_by_ligne[ligne] = cursor.fetchall()
                    
            except Error as e:  # Now Error is properly defined
                print(f"Error fetching products: {e}")
            finally:
                conn.close()
        return products_by_ligne

    @staticmethod
    def add_product(name, cycle_time, ligne):
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO products (name, cycle_time, ligne) VALUES (%s, %s, %s)",
                    (name, cycle_time, ligne)
                )
                conn.commit()
                return True
            except Error as e:  # Now Error is properly defined
                print(f"Error adding product: {e}")
                return False
            finally:
                conn.close()
        return False