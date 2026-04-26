-- הוצאות רגילות
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    amount FLOAT,
    category TEXT,
    description TEXT,
    date TIMESTAMP DEFAULT NOW()
);

-- הוצאות קבועות
CREATE TABLE fixed_expenses (
    id SERIAL PRIMARY KEY,
    amount FLOAT,
    category TEXT,
    description TEXT
);

-- תקציב
CREATE TABLE budget (
    id SERIAL PRIMARY KEY,
    monthly_budget FLOAT
);

-- קטגוריות דינמיות 🔥
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
);