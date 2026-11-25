# MOBILE_FINAL

Backend API cho nền tảng D2C F&B, xây dựng bằng FastAPI. Dự án chạy được bằng Docker trong vài lệnh, hoặc chạy trực tiếp bằng Python 3.13.

## 1. Chạy nhanh bằng Docker (khuyến nghị)

### Yêu cầu

- Docker Engine và Docker Compose plugin (`docker compose version`).
- Cổng `8000` trên máy host chưa bị chiếm. Nếu bị chiếm, đổi mapping trong `docker-compose.yml`, ví dụ `"8080:8000"` rồi truy cập `http://localhost:8080`.

### Khởi động

```bash
docker compose up --build
```

Lệnh này sẽ build image, tạo volume `app-data`, chạy `alembic upgrade head` rồi khởi động API tại `http://localhost:8000`.

Nếu muốn chạy nền:

```bash
docker compose up --build -d
docker compose ps
```

Service `api` sẽ chuyển sang trạng thái `healthy` khi healthcheck gọi `GET /health` thành công.

### Kiểm tra

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/health/ready
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs
curl -fsS http://localhost:8000/v1/ping/
```

Kết quả mong đợi:

- `/health` → `{"status":"ok"}`
- `/health/ready` → `{"status":"ready"}`
- `/docs` → `200`
- `/v1/ping/` → `200`

Giao diện Swagger UI: <http://localhost:8000/docs>  
ReDoc: <http://localhost:8000/redoc>  
OpenAPI JSON: <http://localhost:8000/openapi.json>

> `/docs`, `/redoc` và `/openapi.json` luôn bật, kể cả khi `DEBUG=false`.

### Dừng và khởi động lại

```bash
docker compose logs -f api          # xem log
docker compose restart api          # khởi động lại service
docker compose down                 # dừng container, GIỮ dữ liệu trong volume
docker compose up -d                # chạy lại sau khi down
docker compose down -v              # dừng và XÓA volume (mất dữ liệu SQLite)
```

Dữ liệu SQLite nằm tại `/data/app.db` bên trong named volume `app-data`, nên vẫn tồn tại sau `docker compose down` thông thường. Chỉ `docker compose down -v` mới xóa dữ liệu.

### Kiểm tra migration và database

```bash
docker compose exec api alembic current
docker compose exec api ls -l /data/app.db
```

Revision mong đợi là `ca63adc51b03 (head)`. Container tự chạy `alembic upgrade head` trước khi uvicorn nhận request; không cần gọi `init_db()` thủ công và không nên chạy cả hai cách trên cùng một database.

## 2. Cấu hình

Các biến môi trường được đặt trong block `environment` của `docker-compose.yml`:

| Biến | Giá trị mặc định trong compose | Ý nghĩa |
| --- | --- | --- |
| `DEBUG` | `false` | Tắt reload trong container |
| `HOST` | `0.0.0.0` | Bind địa chỉ cho uvicorn |
| `PORT` | `8000` | Cổng bên trong container |
| `DATABASE_URL` | `sqlite+aiosqlite:////data/app.db` | Đường dẫn tuyệt đối tới file SQLite trong volume |

Bốn dấu `/` trong `sqlite+aiosqlite:////data/app.db` là cú pháp URL cho đường dẫn tuyệt đối `/data/app.db`.

Một số biến khác cũng có thể thêm vào `environment` nếu cần:

```yaml
environment:
  ENVIRONMENT: "production"
  CORS_ORIGINS: '["https://your-frontend.example.com"]'
  CORS_ALLOW_CREDENTIALS: "false"
  ACCESS_TOKEN_EXPIRE_MINUTES: "30"
  REFRESH_TOKEN_EXPIRE_DAYS: "7"
```

Lưu ý:

- `.env` ở máy host **không được copy vào image** nhờ `.dockerignore`. Nếu muốn dùng file env, thêm `env_file: .env` vào service `api` trong `docker-compose.yml`.
- `CORS_ORIGINS` là danh sách JSON. Cấu hình mặc định `["*"]` cùng `CORS_ALLOW_CREDENTIALS=true` không được trình duyệt chấp nhận; hãy khai báo origin cụ thể khi deploy thật.
- `get_settings()` trong `app/config/settings.py` hiện truyền cứng `secret_key`, nên biến môi trường `SECRET_KEY` chưa có tác dụng với ứng dụng. Cần sửa hàm này trước khi dùng secret thật.
- Image chỉ cài dependency runtime từ `pyproject.toml`, không cài extra `dev`.
- Nếu đổi `PORT`, nhớ đổi cả mapping cổng host trong `ports`.
- Nếu chuyển sang Postgres/MySQL, cần thêm driver async tương ứng (ví dụ `asyncpg` hoặc `psycopg[binary]`) vào dependency trước khi đổi `DATABASE_URL`.

## 3. Chạy local không dùng Docker

Yêu cầu Python 3.13 trở lên.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Chạy test:

```bash
pytest
```

Mặc định local dùng `sqlite+aiosqlite:///./app.db`, tức file `app.db` ở thư mục hiện tại. Có thể ghi đè bằng biến môi trường `DATABASE_URL` hoặc file `.env`.

## 4. Cấu trúc file Docker

- `Dockerfile`: base `python:3.13-slim`, chạy ứng dụng với user không phải root, tự migration rồi `exec uvicorn`.
- `.dockerignore`: loại `.env`, database, cache, test và các file không cần thiết khỏi build context.
- `docker-compose.yml`: cấu hình cổng, biến môi trường, volume `app-data` và healthcheck.

Để kiểm tra cấu hình compose trước khi build:

```bash
docker compose config
```
