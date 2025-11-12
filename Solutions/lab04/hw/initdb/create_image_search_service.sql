-- create_image_search_service.sql

-- Create the database for the similarity search service
CREATE DATABASE image_search_service;

-- Connect to the database
\c image_search_service;

-- Enable vectorscale extension
CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;