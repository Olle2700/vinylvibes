-- VinylVibes schema for exams / migrations

CREATE DATABASE IF NOT EXISTS vinylvibes;
USE vinylvibes;

CREATE TABLE IF NOT EXISTS users (
  user_pk CHAR(32) NOT NULL,
  user_email VARCHAR(120) NOT NULL,
  user_password VARCHAR(255) NOT NULL,
  user_username VARCHAR(30) NOT NULL,
  user_first_name VARCHAR(40) NOT NULL,
  user_last_name VARCHAR(40) NOT NULL,
  user_avatar_path VARCHAR(255) NOT NULL,
  user_bio VARCHAR(160) NOT NULL DEFAULT '',
  user_verification_key CHAR(32) NOT NULL DEFAULT '',
  user_verified_at BIGINT UNSIGNED NOT NULL DEFAULT 0,
  user_reset_key CHAR(32) NOT NULL DEFAULT '',
  user_reset_expires BIGINT UNSIGNED NOT NULL DEFAULT 0,
  user_role ENUM('user','admin') NOT NULL DEFAULT 'user',
  user_blocked_at BIGINT UNSIGNED NOT NULL DEFAULT 0,
  user_created_at BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (user_pk),
  UNIQUE KEY uq_users_email (user_email),
  UNIQUE KEY uq_users_username (user_username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS posts (
  post_pk CHAR(32) NOT NULL,
  post_user_fk CHAR(32) NOT NULL,
  post_message VARCHAR(280) NOT NULL,
  post_total_likes BIGINT UNSIGNED NOT NULL DEFAULT 0,
  post_image_path VARCHAR(255) NOT NULL DEFAULT '',
  post_blocked_at BIGINT UNSIGNED NOT NULL DEFAULT 0,
  post_created_at BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (post_pk),
  KEY fk_posts_users (post_user_fk),
  CONSTRAINT fk_posts_users FOREIGN KEY (post_user_fk) REFERENCES users (user_pk) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS post_likes (
  like_pk CHAR(32) NOT NULL,
  like_post_fk CHAR(32) NOT NULL,
  like_user_fk CHAR(32) NOT NULL,
  like_created_at BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (like_pk),
  UNIQUE KEY uq_like (like_post_fk, like_user_fk),
  KEY fk_like_post (like_post_fk),
  KEY fk_like_user (like_user_fk),
  CONSTRAINT fk_like_post FOREIGN KEY (like_post_fk) REFERENCES posts (post_pk) ON DELETE CASCADE,
  CONSTRAINT fk_like_user FOREIGN KEY (like_user_fk) REFERENCES users (user_pk) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS comments (
  comment_pk CHAR(32) NOT NULL,
  comment_post_fk CHAR(32) NOT NULL,
  comment_user_fk CHAR(32) NOT NULL,
  comment_body VARCHAR(240) NOT NULL,
  comment_created_at BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (comment_pk),
  KEY fk_comment_post (comment_post_fk),
  KEY fk_comment_user (comment_user_fk),
  CONSTRAINT fk_comment_post FOREIGN KEY (comment_post_fk) REFERENCES posts (post_pk) ON DELETE CASCADE,
  CONSTRAINT fk_comment_user FOREIGN KEY (comment_user_fk) REFERENCES users (user_pk) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS follows (
  follow_pk CHAR(32) NOT NULL,
  follow_follower_fk CHAR(32) NOT NULL,
  follow_following_fk CHAR(32) NOT NULL,
  follow_created_at BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (follow_pk),
  UNIQUE KEY uq_follow (follow_follower_fk, follow_following_fk),
  KEY fk_follow_follower (follow_follower_fk),
  KEY fk_follow_following (follow_following_fk),
  CONSTRAINT fk_follow_follower FOREIGN KEY (follow_follower_fk) REFERENCES users (user_pk) ON DELETE CASCADE,
  CONSTRAINT fk_follow_following FOREIGN KEY (follow_following_fk) REFERENCES users (user_pk) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Seed admin user (password: admin123)
INSERT INTO users (user_pk, user_email, user_password, user_username, user_first_name, user_last_name, user_avatar_path, user_bio, user_verification_key, user_verified_at, user_reset_key, user_reset_expires, user_role, user_blocked_at, user_created_at)
VALUES ('0000000000000000000000000000admin', 'admin@vinylvibes.test', 'pbkdf2:sha256:1000000$c5tGOjitkyJ2E1ZC$072a4afb07396302d7b80cc4599f7c45ca3ae37997be69dca45cae97bfc3244d', 'admin', 'Admin', '', 'https://avatar.iran.liara.run/public/100', '', '', UNIX_TIMESTAMP(), '', 0, 'admin', 0, UNIX_TIMESTAMP())
ON DUPLICATE KEY UPDATE user_role = 'admin';
