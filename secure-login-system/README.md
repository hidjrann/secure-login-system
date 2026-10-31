# Secure Login System

Python Flask və SQLite əsasında hazırlanmış tədris məqsədli təhlükəsiz giriş sistemi. Layihə Secure SDLC təqdimatı üçün nəzərdə tutulub.

## Funksiyalar

- İstifadəçi qeydiyyatı və giriş
- Werkzeug vasitəsilə parol heşlənməsi (açıq mətn parol saxlanılmır)
- Flask sessiyaları və sessiyanın giriş zamanı yenilənməsi
- Qorunan dashboard və logout
- Login üçün IP əsaslı sorğu limiti: 5 cəhd/dəqiqə
- Flask-WTF CSRF qorunması
- Parametrli SQL sorğuları
- Təhlükəsizlik HTTP başlıqları
- SQLite verilənlər bazası

## 1. Quraşdırma

Python 3.10 və ya daha yeni versiya tövsiyə olunur.

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Asılılıqları quraşdır:
```bash
pip install -r requirements.txt
```

## 2. Gizli açar

Təqdimat və lokal sınaq üçün tətbiqdə müvəqqəti development açarı var. Real yayımlama üçün `SECRET_KEY` mühit dəyişəni ilə güclü, təsadüfi açar təyin edilməlidir.

PowerShell:
```powershell
$env:SECRET_KEY = "buraya-uzun-ve-tesadufi-acar"
```

## 3. İşə salmaq

```bash
python app.py
```

Brauzerdə aç:
http://127.0.0.1:5000

Qeydiyyatdan keç, sonra daxil ol. Dashboard yalnız daxil olmuş istifadəçilər üçün açıqdır.

## 4. Testləri işə salmaq

```bash
pytest -v
```

Testlər qeydiyyatı, parolun heşlənməsini, düzgün/yanlış girişi, boş sahələri, icazəsiz dashboard girişini və istifadəçilərin bir-birinin dashboard məlumatını görməməsini yoxlayır.

Qeyd: Rate-limit qaydasının tətbiqdə konfiqurasiya edilməsi kodda göstərilib. İstehsalat səviyyəsində limitin real davranışını ayrıca inteqrasiya testi ilə yoxlamaq tövsiyə olunur.

## Təhlükəsizlik qeydləri

- `SECRET_KEY` yayımlanmış repozitoriyaya yerləşdirilməməlidir.
- İstehsalatda HTTPS aktiv edilməli və `COOKIE_SECURE=1` seçilməlidir.
- Demo layihə tədris məqsədlidir; real istifadə üçün əlavə təhlükəsizlik auditi, loglama, hesab bərpası, e-poçt təsdiqi, təhlükəsiz deploy və davamlı monitorinq tələb olunur.
- Rate limiting hazırda yaddaş əsaslıdır; bir neçə serverli istehsalat mühitində Redis kimi ortaq storage istifadə edilməlidir.

## Secure SDLC əlaqəsi

| Mərhələ | Layihədə tətbiq |
|---|---|
| Requirements | Güclü parol, autentifikasiya və icazə tələbləri |
| Design | Qeydiyyat, giriş, sessiya və dashboard axını |
| Development | Parol heşlənməsi, parametrli SQL, CSRF qorunması |
| Testing | Pytest ilə funksional və təhlükəsizlik ssenariləri |
| Deployment | Gizli açar, HTTPS və təhlükəsiz cookie konfiqurasiyası |
| Maintenance | Yeniləmələr, loglama və zəifliklərin aradan qaldırılması |
