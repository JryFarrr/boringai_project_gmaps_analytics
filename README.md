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

### 2. Siapkan File .env Mengacu dari File .env.example

```ini
Maps_API_KEY=
OPENAI_API_KEY=
SEARCHAPI_API_KEY=
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

### 4. Jalankan Workflow Executor

```bash
python WorkflowExecutor.py
```

### 5. Server Berjalan di `http://localhost:5000`

## Dokumentasi Swagger

Setelah server berjalan, dokumentasi API dapat diakses melalui:

#### `http://localhost:5000/apidocs`

### `POST /task/input`

### Request Body

#### Request JSON Example

```json
{
  "business_type": "cafe",
  "location": "Surabaya",
  "numberOfLeads": 3,
  "min_rating": 4.0,
  "min_reviews": 50,
  "max_reviews": 100,
  "price_range": "25rb-50rb", 
  "keywords": "cocok buat nugas",
  "business_hours": "anytime"
}
```

| Parameter        | Type    | Required | Description                                                   | Example              |
| ---------------- | ------- | -------- | ------------------------------------------------------------- | -------------------- |
| `business_type`  | string  | Yes      | Jenis bisnis yang akan dicari (misalnya: restoran, kafe, dll) | `"cafe"`             |
| `location`       | string  | Yes      | Lokasi tempat pencarian dilakukan                             | `"Surabaya"`         |
| `numberOfLeads`  | integer | Yes      | Jumlah lead yang diinginkan                                   | `3`                  |
| `min_rating`     | float   | No       | Rating minimal dari tempat yang dicari                        | `4.0`                |
| `min_reviews`    | integer | No       | Jumlah minimal review dari tempat tersebut                    | `50`                 |
| `max_reviews`    | integer | No       | Jumlah maximal review dari tempat tersebut                    | `100`                |
| `price_range`    | string  | No       | Rentang harga dari tempat                                     | `"25rb-50rb" atau "$"`        |
| `keywords`       | string  | No       | Kata kunci tambahan yang relevan dengan kebutuhan pengguna    | `"cocok buat nugas"` |
| `business_hours` | string  | No       | Waktu operasional yang diinginkan (`anytime` / jam tertentu)  | `"anytime"`          |

### `POST /task/search`

### Request Body

#### Request JSON Example

```json
{
  "business_type": "restaurant",
  "location": "Surabaya",
  "numberOfLeads": 10,
  "searchOffset": 0
}
```

| Parameter       | Type    | Required | Description                                              | Example      |
| --------------- | ------- | -------- | -------------------------------------------------------- | ------------ |
| `business_type` | string  | Yes      | Jenis bisnis yang dicari (misalnya: restoran, kafe, dll) | `restaurant` |
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
  "leadCount": 0,
  "numberOfLeads": 3,
  "placeDetails": {
    "address": "Jl. Raya Jemursari No.71, Jemur Wonosari, Kec. Wonocolo, Surabaya, Jawa Timur 60237, Indonesia",
    "businessHours": [
      "Monday: 8:00 AM – 10:00 PM",
      "Tuesday: 8:00 AM – 10:00 PM",
      "Wednesday: 8:00 AM – 10:00 PM",
      "Thursday: 8:00 AM – 10:00 PM",
      "Friday: 8:00 AM – 10:00 PM",
      "Saturday: 8:00 AM – 10:00 PM",
      "Sunday: 8:00 AM – 10:00 PM"
    ],
    "businessType": [
      "cafe",
      "restaurant",
      "food",
      "point_of_interest",
      "store",
      "establishment"
    ],
    "contact": {
      "phone": "(031) 8480367",
      "website": "http://instagram.com/demandailingcafe"
    },
    "location": {
      "lat": -7.3225321,
      "lng": 112.7423232
    },
    "negativeReviews": [
      "The cashier & greater are not friendly.  The smoking area is dirty and smells like a cat's poop."
    ],
    "placeName": "Demandailing Cafe",
    "positiveReviews": [
      "Always like being here...",
      "It was my very first visit to Demandailing Cafe...",
      "Good services and kind staff...",
      "Best pancake I've ever tasted..."
    ],
    "priceRange": "$$",
    "rating": 4.5,
    "totalRatings": 4202
  },
  "skippedCount": 0,
  "constraints": {
    "min_rating": 4.0,
    "min_reviews": 50,
    "max_reviews": 100,
    "price_range": "$$",
    "business_hours": "anytime",
    "keywords": "cocok buat nugas"
  }
}
```

| Parameter                      | Type    | Required | Description                                            | Example                                   |
| ------------------------------ | ------- | -------- | ------------------------------------------------------ | ----------------------------------------- |
| `leadCount`                    | integer | Yes      | Jumlah lead yang telah dianalisis                      | `0`                                       |
| `numberOfLeads`                | integer | Yes      | Jumlah total lead yang ingin dianalisis                | `3`                                       |
| `placeDetails`                 | object  | Yes      | Objek yang berisi informasi lengkap mengenai tempat    | `{...}`                                   |
| `placeDetails.placeName`       | string  | Yes      | Nama tempat bisnis                                     | `"Demandailing Cafe"`                     |
| `placeDetails.address`         | string  | No       | Alamat lengkap tempat bisnis                           | `"Jl. Raya Jemursari No.71, ..."`         |
| `placeDetails.businessHours`   | array   | No       | Jam operasional bisnis                                 | `[ "Monday: 8:00 AM – 10:00 PM", ... ]`   |
| `placeDetails.businessType`    | array   | No       | Jenis-jenis bisnis yang teridentifikasi                | `["cafe", "restaurant", ...]`             |
| `placeDetails.contact`         | object  | No       | Informasi kontak bisnis                                | `{ "phone": "...", "website": "..." }`    |
| `placeDetails.contact.phone`   | string  | No       | Nomor telepon tempat bisnis                            | `"(031) 8480367"`                         |
| `placeDetails.contact.website` | string  | No       | Website resmi dari tempat bisnis                       | `"http://instagram.com/demandailingcafe"` |
| `placeDetails.location`        | object  | No       | Lokasi geografis bisnis (latitude & longitude)         | `{ "lat": -7.32253, "lng": 112.74232 }`   |
| `placeDetails.positiveReviews` | array   | No       | Review positif dari pelanggan                          | `["Great food!", "Nice place."]`          |
| `placeDetails.negativeReviews` | array   | No       | Review negatif dari pelanggan                          | `["Bad service."]`                        |
| `placeDetails.priceRange`      | string  | No       | Rentang harga dari bisnis                              | `"$$"`                                    |
| `placeDetails.rating`          | float   | No       | Rating rata-rata dari pelanggan                        | `4.5`                                     |
| `placeDetails.totalRatings`    | integer | No       | Jumlah total rating yang diterima                      | `4202`                                    |
| `skippedCount`                 | integer | No       | Jumlah tempat yang dilewati karena tidak sesuai filter | `0`                                       |
| `constraints`                  | object  | No       | Syarat/parameter filtering pencarian                   | `{...}`                                   |
| `constraints.min_rating`       | float   | No       | Rating minimum tempat                                  | `4.0`                                     |
| `constraints.min_reviews`      | integer | No       | Jumlah review minimum                                  | `50`                                      |
| `constraints.max_reviews`      | integer | No       | Jumlah review maximum                                  | `100`                                     |
| `constraints.price_range`      | string  | No       | Rentang harga yang diinginkan                          | `"$$"`                                    |
| `constraints.business_hours`   | string  | No       | Waktu operasional yang diinginkan                      | `"anytime"`                               |
| `constraints.keywords`         | string  | No       | Kata kunci relevan untuk analisis                      | `"cocok buat nugas"`                      |

### `POST /task/control`

### Request Body

#### Request JSON Example

```json
{
  "leadCount": 5,
  "numberOfLeads": 10,
  "remainingPlaceIds": ["placeId1", "placeId2", "placeId3"],
  "searchOffset": 2,
  "nextPageToken": "nextPageTokenExample",
  "business_type": "restaurant",
  "location": "New York, NY",
  "skippedConstraints": true,
  "skippedCount": 1
}
```

| Parameter            | Type    | Required | Description                                                       | Example                    |
| -------------------- | ------- | -------- | ----------------------------------------------------------------- | -------------------------- |
| `leadCount`          | integer | Yes      | Jumlah lead yang sudah berhasil dikumpulkan                       | `5`                        |
| `numberOfLeads`      | integer | Yes      | Jumlah total lead yang ingin dikumpulkan                          | `10`                       |
| `remainingPlaceIds`  | array   | No       | Daftar `place_id` yang belum diproses                             | `["placeId1", "placeId2"]` |
| `searchOffset`       | integer | No       | Posisi offset pencarian berikutnya dalam pagination               | `2`                        |
| `nextPageToken`      | string  | No       | Token halaman berikutnya dari Google Places API                   | `"nextPageTokenExample"`   |
| `business_type`      | string  | No       | Jenis bisnis yang sedang diproses                                 | `"restaurant"`             |
| `location`           | string  | No       | Lokasi dari pencarian lead                                        | `"New York, NY"`           |
| `skippedConstraints` | boolean | No       | Apakah constraint dilewati (misalnya min_rating, reviews, dll)    | `true`                     |
| `skippedCount`       | integer | No       | Jumlah tempat yang dilewati karena tidak sesuai dengan constraint | `1`                        |
