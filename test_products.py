from models.product import Product

if __name__ == "__main__":
    print("Testing product database connection...")
    products = Product.get_products_by_ligne()
    print("\nProducts by production line:")
    for ligne, items in products.items():
        print(f"\n{ligne}:")
        for product in items:
            print(f"  - {product['name']} (Cycle: {product['cycle_time']}s)")
    print("\nTest complete")