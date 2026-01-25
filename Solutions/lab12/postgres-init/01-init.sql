CREATE TABLE exchange_rates (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(255) NOT NULL,
    rate DECIMAL(10, 4) NOT NULL
);

CREATE TABLE models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    test_performance FLOAT NOT NULL,
    training_size INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)