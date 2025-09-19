# FastAPI REST API Örnek Projesi

Bu proje, FastAPI kullanılarak geliştirilmiş örnek bir REST API uygulamasıdır.

## Özellikler

- ✅ CRUD işlemleri (Create, Read, Update, Delete)
- ✅ Pydantic ile veri validasyonu
- ✅ Otomatik API dokümantasyonu (Swagger/OpenAPI)
- ✅ SQLite veritabanı entegrasyonu
- ✅ Async/await desteği

## Kurulum

1. Projeyi klonlayın:
```bash
git clone <repo-url>
cd fastapi-rest-api
```

2. Sanal ortam oluşturun:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

3. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

## Çalıştırma

```bash
uvicorn main:app --reload
```

API dokümantasyonu: http://localhost:8000/docs

## API Endpoints

- `GET /items/` - Tüm öğeleri listele
- `POST /items/` - Yeni öğe oluştur
- `GET /items/{id}` - Belirli bir öğeyi getir
- `PUT /items/{id}` - Öğeyi güncelle
