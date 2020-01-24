DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS meal;
DROP TABLE IF EXISTS recipe;
DROP TABLE IF EXISTS ingredient;
DROP TABLE IF EXISTS mealRecipeRelationship;
DROP TABLE IF EXISTS recipeIngredientRelationship;


--meals, recipes, and ingredients are unique to each user. 
CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

--
CREATE TABLE meal (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE recipe (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
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
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  name_key TEXT NOT NULL UNIQUE, --no whitespace, lowercase
  portion_size FLOAT(2) NOT NULL,
  portion_size_unit TEXT CHECK ( portion_size_unit in ('g', 'kg', 'oz', 'lb', 'cup', 'ml', 'l', 'gal', 'T', 't', 'in', 'unit') ) NOT NULL,
  protein FLOAT(1) NOT NULL,
  fat FLOAT(1) NOT NULL,
  carbs FLOAT(1) NOT NULL,
  cals INT NOT NULL,
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
