DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS meal;
DROP TABLE IF EXISTS recipe;
DROP TABLE IF EXISTS ingredient;
DROP TABLE IF EXISTS mealRecipeRelationship;
DROP TABLE IF EXISTS recipeIngredientRelationship;


--meals and recipes are unique to each user. Ingredients will be prepopulated.
CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE meal (
  id INTEGER PRIMARY KEY,
  author_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE recipe (
  id INTEGER PRIMARY KEY,
  author_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  servings INTEGER NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

/*
Primary key is name_key (text entry, whitespaces substituted by dash) because the expectation is to have
only a few hundred ingredients max, which is reasonable.
*/
CREATE TABLE ingredient (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  name_key TEXT NOT NULL UNIQUE, --no whitespace, lowercase
  portion_size FLOAT(2) NOT NULL,
  portion_size_unit TEXT CHECK ( portion_size_unit in ('g', 'kg', 'oz', 'lb', 'cup', 'ml', 'l', 'gal', 'T', 't', 'in', 'unit') ) NOT NULL,
  portion_converted FLOAT(2) NOT NULL, --will be only in grams or in mls
  protein FLOAT(1) NOT NULL,
  fat FLOAT(1) NOT NULL,
  carbs FLOAT(1) NOT NULL,
  calories INT NOT NULL,
  price INT, --this is in cents to avoid float representation issues
  price_size FLOAT(2), --{{1.5}} in i.5lb bag for instance
  price_size_unit TEXT CHECK ( portion_size_unit in ('g', 'kg', 'oz', 'lb', 'cup', 'ml', 'l', 'gal', 'T', 't', 'in', 'unit') ),
  price_converted FLOAT(2), --price converted to g or ml
  tag TEXT CHECK (tag in ('carbs', 'fats', 'proteins', 'vegetables', 'legumes', 'fruit', 'nuts', 'sauces', 'dairy', 'spices', 'others')),
  notes TEXT
);

CREATE INDEX idx_name ON ingredient(name_key)
;

--these are the junction tables
CREATE TABLE mealRecipeRelationship(
    mealID INTEGER NOT NULL,
    recipeID INTEGER NOT NULL,
    FOREIGN KEY (mealID) REFERENCES meal(id), 
    FOREIGN KEY (recipeID) REFERENCES recipe(id),
    UNIQUE (mealID, recipeID)
);

CREATE TABLE recipeIngredientRelationship(
    recipeID INTEGER NOT NULL,
    ingredientID INTEGER NOT NULL,
    quantity FLOAT(2) NOT NULL,
    units TEXT CHECK ( units in ('g', 'kg', 'oz', 'lb', 'cup', 'ml', 'l', 'gal', 'T', 't', 'in', 'unit') ) NOT NULL,
    FOREIGN KEY (recipeID) REFERENCES recipe(id),
    FOREIGN KEY (ingredientID) REFERENCES ingredient(id),
    UNIQUE (recipeID, ingredientID)
);
