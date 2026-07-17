-- app_user: role ứng dụng dùng runtime; KHÔNG bypass RLS
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user LOGIN PASSWORD 'appdevpass' NOBYPASSRLS;
  END IF;
END $$;
GRANT CONNECT ON DATABASE edmicro TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
-- Quyền bảng mặc định cấp cho bảng tạo sau (migration owner tạo bảng)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
