from app import create_app
app = create_app()
with app.test_client() as c:
    c.post('/login', data={'username': 'admin', 'password': 'Admin@123'})
    for status in ['', 'OPEN', 'REVIEWING', 'RESOLVED', 'DISMISSED']:
        resp = c.get(f'/api/alerts?status={status}&per_page=50')
        data = resp.get_json()
        label = status if status else 'ALL'
        total = data.get('total', 0) if isinstance(data, dict) else 'ERROR'
        print(f'{label}: {total} alerts (status_code={resp.status_code})')
