def test_create_order_with_materials(client, db, admin_token, senior_user):
    """Создание заказа с резервированием материалов"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 1. Создаем материал
    material_response = client.post("/api/v1/inventory/materials/", 
        json={
            "sku": "TEST-001",
            "name": "Тестовый материал",
            "unit": "pcs",
            "min_quantity": 10,
            "current_quantity": 100,
            "cost_price": 100.50
        },
        headers=headers
    )
    material_id = material_response.json()["id"]
    
    # 2. Создаем продукт
    product_response = client.post("/api/v1/assembly/products/",
        json={
            "name": "Тестовый продукт",
            "code": "TEST-PROD",
            "default_time": 120
        },
        headers=headers
    )
    product_id = product_response.json()["id"]
    
    # 3. Добавляем материал в BOM
    bom_response = client.post(f"/api/v1/assembly/products/{product_id}/materials",
        json={
            "material_id": material_id,
            "quantity_required": 5
        },
        headers=headers
    )
    
    # 4. Создаем заказ
    order_response = client.post("/api/v1/assembly/orders/",
        json={
            "product_id": product_id,
            "quantity": 2,
            "priority": "medium",
            "client_name": "Тестовый клиент"
        },
        headers=headers
    )
    
    assert order_response.status_code == status.HTTP_200_OK
    order_data = order_response.json()
    assert order_data["order_number"].startswith("ORD-")
    assert order_data["status"] == "draft"
    
    # 5. Проверяем резервирование материалов
    transactions_response = client.get(
        f"/api/v1/inventory/transactions?order_id={order_data['id']}",
        headers=headers
    )
    
    transactions = transactions_response.json()
    assert len(transactions) == 1
    assert transactions[0]["transaction_type"] == "reservation"
    assert float(transactions[0]["quantity"]) == 10.0  # 5 * 2