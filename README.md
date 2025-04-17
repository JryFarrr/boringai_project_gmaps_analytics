# BoringAI GMaps Analytics

Sebuah API service yang dapat mengumpulkan data bisnis dari Google Maps, menganalisis informasi bisnis tersebut menggunakan OpenAI, dan memberikan insight berupa kekuatan, kelemahan, serta kecocokan dengan kriteria tertentu.

---

## Fitur Utama

- **Pencarian Bisnis** berdasarkan lokasi dan jenis usaha.
- **Analisis Otomatis** menggunakan OpenAI untuk memberikan insight bisnis.
- **Kontrol Alur Kerja** fleksibel untuk scraping dan analisis.
- **Swagger UI** dokumentasi interaktif.

---

## Packages yang Diperlukan

Sebelum menjalankan proyek ini, pastikan semua dependensi berikut ter-install. Gunakan `pip` atau `requirements.txt`.

### Install dari `requirements.txt`

```bash
pip install -r requirements.txt
```

## Cara Menjalankan API

### 1. Clone repository

```bash
git clone https://github.com/JryFarrr/boringai_project_gmaps_analytics.git
cd boringai_project_gmaps_analytics

```

### 2. Siapkan File .env

```ini
GOOGLE_MAPS_API_KEY=
OPENROUTER_API_KEY=
OPENAI_API_KEY=
DEFAULT_REFERER_URL=https://your-website.com
DEFAULT_SITE_NAME=Map Leads AI
DEFAULT_API_PROVIDER=openai
DEFAULT_OPENAI_MODEL=gpt-4o-mini
DEFAULT_OPENROUTER_MODEL=openai/gpt-4o-mini
```

### 3. Jalankan Server

```bash
python app.py
```

### 4. Server Berjalan di `http://localhost:5000`

## Dokumentasi Swagger

Setelah server berjalan, dokumentasi API dapat diakses melalui:

#### `http://localhost:5000/apidocs`

### `POST /task/input`

### Request Body

#### Request JSON Example

```json
{
  "businessType": "restaurant",
  "location": "Surabaya",
  "numberOfLeads": 10
}
```

| Parameter       | Type    | Required | Description                                                   | Example        |
| --------------- | ------- | -------- | ------------------------------------------------------------- | -------------- |
| `businessType`  | string  | Yes      | Jenis bisnis yang akan dicari (misalnya: restoran, kafe, dll) | `"restaurant"` |
| `location`      | string  | Yes      | Lokasi tempat pencarian dilakukan                             | `"Surabaya"`   |
| `numberOfLeads` | integer | Yes      | Jumlah lead yang diinginkan                                   | `10`           |

### `POST /task/search`

### Request Body

#### Request JSON Example

```json
{
  "businessType": "restaurant",
  "location": "Surabaya",
  "numberOfLeads": 10,
  "searchOffset": 0
}
```

| Parameter       | Type    | Required | Description                                              | Example      |
| --------------- | ------- | -------- | -------------------------------------------------------- | ------------ |
| `businessType`  | string  | Yes      | Jenis bisnis yang dicari (misalnya: restoran, kafe, dll) | `restaurant` |
| `location`      | string  | Yes      | Lokasi pencarian                                         | `Surabaya`   |
| `numberOfLeads` | integer | Yes      | Jumlah lead yang diinginkan                              | `10`         |
| `searchOffset`  | integer | No       | Offset untuk pencarian lebih lanjut                      | `0`          |

### `POST /task/scrape`

### Request Body

#### Request JSON Example

```json
{
  "placeId": "ChIJhS6qhGT51y0RUCoksi_dipo",
  "numberOfLeads": 10
}
```

| Parameter       | Type    | Required | Description                  | Example                       |
| --------------- | ------- | -------- | ---------------------------- | ----------------------------- |
| `placeId`       | string  | Yes      | ID tempat dari Google Places | `ChIJhS6qhGT51y0RUCoksi_dipo` |
| `numberOfLeads` | integer | Yes      | Jumlah lead yang diinginkan  | `10`                          |

### `POST /task/analyze`

### Request Body

#### Request JSON Example

```json
{
  "placeDetails": {
    "placeName": "Cafe Delight",
    "contact": {
      "phone": "123-456-7890",
      "website": "https://cafedelight.com"
    },
    "priceRange": "$$",
    "positiveReviews": ["Great vibe"],
    "negativeReviews": ["Crowded"]
  },
  "leadCount": 0
}
```

| Parameter                      | Type    | Required | Description                                | Example                   |
| ------------------------------ | ------- | -------- | ------------------------------------------ | ------------------------- |
| `placeDetails`                 | object  | Yes      | Objek yang berisi informasi detail bisnis  | `{...}`                   |
| `placeDetails.placeName`       | string  | Yes      | Nama bisnis atau tempat                    | `Cafe Delight`            |
| `placeDetails.contact`         | object  | Yes      | Informasi kontak bisnis                    | `{...}`                   |
| `placeDetails.contact.phone`   | string  | No       | Nomor telepon bisnis                       | `123-456-7890`            |
| `placeDetails.contact.website` | string  | No       | Website resmi bisnis                       | `https://cafedelight.com` |
| `placeDetails.priceRange`      | string  | No       | Rentang harga                              | `$$`                      |
| `placeDetails.positiveReviews` | array   | No       | Daftar ulasan positif dari pelanggan       | `["Great vibe"]`          |
| `placeDetails.negativeReviews` | array   | No       | Daftar ulasan negatif dari pelanggan       | `["Crowded"]`             |
| `leadCount`                    | integer | Yes      | Jumlah lead yang sudah diproses sebelumnya | `0`                       |

### `POST /task/control`

### Request Body

#### Request JSON Example

```json
{
  "leadCount": 1,
  "numberOfLeads": 10,
  "remainingPlaceIds": ["def456", "ghi789"]
}
```

| Parameter           | Type    | Required | Description                           | Example                |
| ------------------- | ------- | -------- | ------------------------------------- | ---------------------- |
| `leadCount`         | integer | Yes      | Jumlah lead yang sudah diproses       | `1`                    |
| `numberOfLeads`     | integer | Yes      | Jumlah total lead yang ingin diproses | `10`                   |
| `remainingPlaceIds` | array   | No       | Daftar Place ID yang belum diproses   | `["def456", "ghi789"]` |
