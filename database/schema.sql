CREATE DATABASE IF NOT EXISTS conversion_app;
  DEFAULT CHARACTER SET utf8mb4;

USE conversion_app;

CREATE TABLE IF NOT EXISTS `media_type` (`type_id` int AUTO_INCREMENT PRIMARY KEY, `type_name` varchar(50) UNIQUE NOT NULL)

CREATE TABLE IF NOT EXISTS `format` (`format_id` int AUTO_INCREMENT PRIMARY KEY, `format_name` varchar(20) UNIQUE NOT NULL)

CREATE TABLE IF NOT EXISTS `tag` (`tag_id` int AUTO_INCREMENT PRIMARY KEY, `tag_name` varchar(50) UNIQUE NOT NULL)

CREATE TABLE IF NOT EXISTS `media`
    `media_id` int AUTO_INCREMENT PRIMARY KEY,
    `file_name` varchar(255) NOT NULL,
    `media_link` varchar(500) NOT NULL,
    `type_id` int NOT NULL,
    `date_of_creation` datetime NOT NULL,
    `notes` text,
    `stored_at` varchar(500),
    `is_downloaded` boolean NOT NULL,
    FOREIGN KEY (`type_id`) REFERENCES `media_type`(`type_id`)

CREATE TABLE IF NOT EXISTS `media_tag`
    `media_id` int NOT NULL,
    `tag_id` int NOT NULL,
    PRIMARY KEY (`media_id`, `tag_id`),
    FOREIGN KEY (`media_id`) REFERENCES `media`(`media_id`),
    FOREIGN KEY (`tag_id`) REFERENCES `tag`(`tag_id`)

CREATE TABLE IF NOT EXISTS `conversion`
    `conversion_id` int AUTO_INCREMENT PRIMARY KEY,
    `media_id` int NOT NULL,
    `format_id` int NOT NULL,
    `output_path` varchar(500),
    `converted_at` datetime NOT NULL,
    `file_size_mb` decimal(10,2),
    FOREIGN KEY (`media_id`) REFERENCES `media`(`media_id`),
    FOREIGN KEY (`format_id`) REFERENCES `format`(`format_id`)
