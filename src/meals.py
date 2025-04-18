class Meal:
    def __init__(self, id, mealname, note, stars, ingredients=None):
        self.id = id
        self.mealname = mealname
        self.note = note
        self.stars = stars
        self.ingredients = ingredients if ingredients else []  # Standard: leere Liste

    @classmethod
    def from_db_row(cls, row):
        """
        Erstellt eine Meal-Instanz aus einer SQL-Datenbank-Zeile.
        row = (meal_id, mealname, note, stars, ingredients)
        """
        meal_id, mealname, note, stars, ingredients = row

        return cls(meal_id, mealname, note, stars, ingredients)


    def to_dict(self):
        """Wandelt das Objekt in ein JSON-serialisierbares Dictionary um."""
        return {
            "id": self.id,
            "mealname": self.mealname,
            "note": self.note,
            "stars": self.stars,
            "ingredients": self.ingredients  # Zutaten-Liste als Dictionaries
        }
