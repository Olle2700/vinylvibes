-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: mariadb
-- Generation Time: Nov 03, 2025 at 10:58 PM
-- Server version: 10.6.20-MariaDB-ubu2004
-- PHP Version: 8.2.27

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `x`
--

-- --------------------------------------------------------

--
-- Table structure for table `posts`
--

CREATE TABLE `posts` (
  `post_pk` char(32) NOT NULL,
  `post_user_fk` char(32) NOT NULL,
  `post_message` varchar(280) NOT NULL,
  `post_total_likes` bigint(20) UNSIGNED NOT NULL,
  `post_image_path` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `posts`
--

INSERT INTO `posts` (`post_pk`, `post_user_fk`, `post_message`, `post_total_likes`, `post_image_path`) VALUES
('1e5ecc804e1f46bc8e723437bf4bfc4b', '225a9fc15b8f409aa5c8ee7eafee516b', 'And this just works!', 0, 'post_3.jpg'),
('258aeac7242348058c8c36f025b10fd5', '225a9fc15b8f409aa5c8ee7eafee516b', 'tes5', 0, ''),
('28dd4c1671634d73acd29a0ab109bef1', '805a39cd8c854ee8a83555a308645bf5', 'My first super life !', 0, 'post_3.jpg'),
('299323cf81924589b0de265e715a1f9e', '225a9fc15b8f409aa5c8ee7eafee516b', 'test3', 0, 'post_1.jpg'),
('3cb78d73518c4c01a29ad33d196ce962', '225a9fc15b8f409aa5c8ee7eafee516b', 'This is new', 0, ''),
('3e4f0c3ab65344d8b79c849400418758', '225a9fc15b8f409aa5c8ee7eafee516b', 'test1', 0, ''),
('3f534678ba324c3aa2624c1f118573f7', '6b48c6095913402eb4841529830e5415', 'dfdfd', 0, ''),
('50293af4d1f64798af9b7dfcbf5ed3e7', '225a9fc15b8f409aa5c8ee7eafee516b', 'new', 0, ''),
('5b147eb4f0064bd9be7f18e6be2b3347', '225a9fc15b8f409aa5c8ee7eafee516b', 'First great test', 0, ''),
('616c38c6e9e14406a92439e2d81490fc', '225a9fc15b8f409aa5c8ee7eafee516b', 'A browser', 0, ''),
('63ed90b8cafc47fa9a3253fa1ecfeb04', '225a9fc15b8f409aa5c8ee7eafee516b', 'this', 0, ''),
('69d3ed14f15047139b6cd8bd8180c104', '59ac8f8892bc45528a631d4415151f13', 'This is Daniel\'s post', 0, ''),
('6b7bc6fd2b57486db21325030f63fd90', '6b48c6095913402eb4841529830e5415', 'erere', 0, ''),
('79c5470b54da40f5ac19729738b37a38', '6b48c6095913402eb4841529830e5415', 'dfdfd', 0, ''),
('7d6f40e626c54efaa32494bce5f739d7', '88a93bb5267e443eb0047f421a7a2f34', 'test', 0, 'post_2.jpg'),
('99fefea24ea5419da19ed1f8cf8e9499', '225a9fc15b8f409aa5c8ee7eafee516b', 'wow', 0, 'post_1.jpg'),
('ad95e1d3f62f4d07b7bf9e3e6d4dd527', '225a9fc15b8f409aa5c8ee7eafee516b', 'And this just works!', 0, ''),
('b4b23963a6a4479e918e66f47baef200', '225a9fc15b8f409aa5c8ee7eafee516b', 'test1', 0, ''),
('b8f59662ce5b4b58bf19a5fe0eda3122', '225a9fc15b8f409aa5c8ee7eafee516b', 'test2', 0, ''),
('bcaa6df8880e411a9c25deaafae2314a', '225a9fc15b8f409aa5c8ee7eafee516b', 'test4', 0, ''),
('e40967338e8c466985dbde4e3f9c712a', '225a9fc15b8f409aa5c8ee7eafee516b', 'Testing', 0, ''),
('efaf8b6f98be4a7b8cc7a75d0f83578c', '225a9fc15b8f409aa5c8ee7eafee516b', 'test', 0, '');

-- --------------------------------------------------------

--
-- Table structure for table `trends`
--

CREATE TABLE `trends` (
  `trend_pk` char(32) NOT NULL,
  `trend_title` varchar(100) NOT NULL,
  `trend_message` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `trends`
--

INSERT INTO `trends` (`trend_pk`, `trend_title`, `trend_message`) VALUES
('6543c995d1af4ebcbd5280a4afaa1e2c', 'Politics are rotten', 'Everyone talks and only a few try to do something'),
('8343c995d1af4ebcbd5280a6afaa1e2d', 'New rocket to the moon', 'A new rocket has been sent towards the moon, but id didn\'t make it');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_pk` char(32) NOT NULL,
  `user_email` varchar(100) NOT NULL,
  `user_password` varchar(255) NOT NULL,
  `user_username` varchar(20) NOT NULL,
  `user_first_name` varchar(20) NOT NULL,
  `user_last_name` varchar(20) NOT NULL DEFAULT '',
  `user_avatar_path` varchar(50) NOT NULL,
  `user_verification_key` char(32) NOT NULL,
  `user_verified_at` bigint(20) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_pk`, `user_email`, `user_password`, `user_username`, `user_first_name`, `user_last_name`, `user_avatar_path`, `user_verification_key`, `user_verified_at`) VALUES
('21e66977ccb74fdbb6cbdb3e7e3a12cb', 'daniel@gmail.com', 'scrypt:32768:8:1$OSL1Z4fWygxh9s2t$c5404c596d389e4fc1fc36a2853ee5f662ab4903476210424a325c50fa7ac64729716f3156687d789c6d895b9876ef069ced40e0e84a7372ca758ffa3a692960', 'daniel', 'Daniel', '', 'avatar_2.jpg', 'c29fa5894f224964953801c925a7cac5', 0),
('225a9fc15b8f409aa5c8ee7eafee516b', 'a@aaa.com', 'scrypt:32768:8:1$wnse70hQwhCvR9tC$724c32a91b5f277201afbb141f9293a93168327df5c9124f482d3c32b8dff991c41629f477dfaee021965f9b15318a4257aad2e933101a4c998ef3c346fc84e4', 'santisss', 'Tester', '', 'avatar_1.jpg', '', 455656),
('59ac8f8892bc45528a631d4415151f13', 'terese@gmail.com', 'scrypt:32768:8:1$Tq056RbRH27Mc9g3$84810a2576e4828498be40c7f51f33e59d19d136e0c5c12e31fb676f3141934c639e088530f9be4ce682cbdfd4eaec34e1220fa7121bf8779e7de0bff29115b9', 'Mily', 'Mille', '', '', '', 45665656),
('6b48c6095913402eb4841529830e5415', 'a@a.com', 'scrypt:32768:8:1$rRjuDGIwaA31YlPi$f73f9a059fb3757ba6724d9c94e2a192d8b8d59fcd18d7b11c57e508f1b9cfb94bb7c6fd4f8d632b777e31cd47aef9c95adcad2451786cbb7e7c073fe8cbaf3a', 'Sofi', 'Sofie', '', '', '', 45445),
('805a39cd8c854ee8a83555a308645bf5', 'fullflaskdemomail@gmail.com', 'scrypt:32768:8:1$VlBgiW1xFsZuKRML$a5f61d62ac3f45d42c58cf8362637e717793b8760f026b1b47b7bfec47037abbe13e1c20e8bdc66fc03cc153d0bcf6185e15cf25ad58eb9d344267882dd7e78c', 'santiago', 'Santiago', '', 'avatar_3.jpg', '', 565656),
('88a93bb5267e443eb0047f421a7a2f34', 'santi@gmail.com', 'scrypt:32768:8:1$PEIO0eliDPqnCCbw$acb791128831bc90030ac363e4b76db196689bd99c1ccde5c2c20a7d4fe909e07129f3f4fd4f086e347375edbb8229e9ba5dc126cc14f6107fb1fc2abf6498f8', 'gustav', 'Gustav', '', 'avatar_2.jpg', '', 54654564);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `posts`
--
ALTER TABLE `posts`
  ADD PRIMARY KEY (`post_pk`),
  ADD UNIQUE KEY `post_pk` (`post_pk`);

--
-- Indexes for table `trends`
--
ALTER TABLE `trends`
  ADD UNIQUE KEY `trend_pk` (`trend_pk`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_pk`),
  ADD UNIQUE KEY `user_pk` (`user_pk`),
  ADD UNIQUE KEY `user_email` (`user_email`),
  ADD UNIQUE KEY `user_name` (`user_username`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
