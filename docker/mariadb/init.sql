-- Creates the four extra per-site databases (the first, wp1, is created
-- automatically by the official mariadb image from MARIADB_DATABASE) and
-- grants the shared demo WordPress user access to all five.
CREATE DATABASE IF NOT EXISTS wp2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS wp3 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS wp4 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS wp5 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON wp1.* TO 'wpuser'@'%';
GRANT ALL PRIVILEGES ON wp2.* TO 'wpuser'@'%';
GRANT ALL PRIVILEGES ON wp3.* TO 'wpuser'@'%';
GRANT ALL PRIVILEGES ON wp4.* TO 'wpuser'@'%';
GRANT ALL PRIVILEGES ON wp5.* TO 'wpuser'@'%';
FLUSH PRIVILEGES;
