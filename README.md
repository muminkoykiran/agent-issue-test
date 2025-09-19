# FastAPI REST API Örnek Projesi

Bu proje, FastAPI kullanarak basit bir REST API örneğidir. Kullanıcı yönetimi için temel CRUD operasyonlarını içerir.

## Özellikler

- ✅ Kullanıcı oluşturma, listeleme, güncelleme ve silme
- ✅ Pydantic ile veri doğrulama
- ✅ Otomatik API dokümantasyonu (Swagger UI)
- ✅ SQLite veritabanı entegrasyonu
- ✅ Async/await desteği

## Kurulum

1. Gereksinimleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Uygulamayı başlatın:
```bash
uvicorn main:app --reload
```

## API Endpoints

- `GET /` - Ana sayfa
- `GET /users` - Tüm kullanıcıları listele
- `POST /users` - Yeni kullanıcı oluştur
- `GET /users/{user_id}` - Belirli bir kullanıcıyı getir
- `PUT /users/{user_id}` - Kullanıcı bilgilerini güncelle
- `DELETE /users/{user_id}` - Kullanıcıyı sil

## API Dokümantasyonu

Uygulama çalıştıktan sonra aşağıdaki adreslerde API dokümantasyonuna erişebilirsiniz:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Teknolojiler

- **FastAPI** - Modern, hızlı web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Veri doğrulama
