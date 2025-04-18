from flask import Flask, request, abort, jsonify
import psycopg2
import os
from dotenv import load_dotenv
from meals import Meal
from flask_cors import CORS


# .env-Datei laden (enthält die DB-Zugangsdaten)
load_dotenv()

# Flask-App erstellen
app = Flask(__name__)


# Datenbank-Verbindungsfunktion
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

@app.route('/all_meals', methods=['GET'])
def get_all_meals():
    try:
        # Verbindung zur Datenbank herstellen
        conn = get_db_connection()
        cur = conn.cursor()

        # Abfrage, um alle Gerichte zusammen mit ihren Zutaten und Mengen abzurufen
        cur.execute("""
            SELECT m.id, m.mealname, m.note, m.stars, 
            STRING_AGG(i.ingredient || ' (' || mi.amount || ' ' || mi.unit || ')', ', ') AS ingredients
            FROM meals m
            LEFT JOIN meal_ingredients mi ON m.id = mi.meal_id
            LEFT JOIN ingredients i ON mi.ingredient_id = i.id
            GROUP BY m.id, m.mealname, m.note, m.stars
            ORDER BY m.id;
        """)
        meals = [Meal.from_db_row(row) for row in cur.fetchall()]

        cur.close()
        conn.close()

        return jsonify([meal.to_dict() for meal in meals])

    except Exception as e:
        return jsonify({"error": f"Datenbankfehler: {str(e)}"}), 500


@app.route('/meal/<int:meal_id>', methods=['GET'])
def get_meal_by_id(meal_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Mahlzeit-Infos abrufen
        cur.execute("""
            SELECT id, mealname, note, stars 
            FROM meals
            WHERE id = %s
        """, (meal_id,))
        meal_row = cur.fetchone()

        if not meal_row:
            return jsonify({"error": "Gericht nicht gefunden"}), 404

        meal_id, mealname, note, stars = meal_row

        # Zutaten abrufen
        cur.execute("""
            SELECT i.ingredient, mi.amount, mi.unit
            FROM meal_ingredients mi
            JOIN ingredients i ON mi.ingredient_id = i.id
            WHERE mi.meal_id = %s
        """, (meal_id,))
        ingredients = cur.fetchall()  # Liste von Tupeln [(Zutat, Menge), (Zutat, Menge)]

        cur.close()
        conn.close()

        # Meal-Objekt mit Zutaten erstellen
        meal = Meal(meal_id, mealname, note, stars, [{"ingredient": ing, "amount": amt, "unit": unt} for ing, amt, unt in ingredients])

        return jsonify(meal.to_dict())

    except Exception as e:
        return jsonify({"error": f"Datenbankfehler: {str(e)}"}), 500


@app.route('/add_meal', methods=['POST'])
def add_meal():
    try:
        data = request.get_json()  # Holt die Daten aus dem Request-Body
        
        # Extrahiert die Mahlzeitinformationen
        mealname = data.get("mealname")
        note = data.get("note")
        stars = data.get("stars")
        ingredients = data.get("ingredients")  # Liste von Zutaten

        # Verbindung zur DB herstellen
        conn = get_db_connection()
        cur = conn.cursor()

        # Einfügen der Mahlzeit in die Mahlzeitentabelle
        cur.execute("""
            INSERT INTO meals (mealname, note, stars)
            VALUES (%s, %s, %s) RETURNING id
        """, (mealname, note, stars))

        meal_id = cur.fetchone()[0]  # Holt die neu erstellte Mahlzeit-ID

        # Zutaten und Menge hinzufügen
        for ingredient in ingredients:
            ingredient_name = ingredient["ingredient"]
            amount = ingredient["amount"]
            unit = ingredient["unit"]
            # Prüfe, ob die Zutat bereits existiert
            cur.execute("""
                SELECT id FROM ingredients WHERE ingredient = %s
            """, (ingredient_name,))
            ingredient_row = cur.fetchone()

            # Überprüfe, ob der Rückgabewert ein Tupel oder None ist
            if ingredient_row is None:
                # Falls die Zutat nicht existiert, füge sie hinzu
                cur.execute("""
                    INSERT INTO ingredients (ingredient)
                    VALUES (%s) RETURNING id
                """, (ingredient_name,))
                ingredient_row = cur.fetchone()  # Hier sicherstellen, dass wir eine Zeile bekommen

            # Extrahiere die ID aus der zurückgegebenen Zeile
            ingredient_id = ingredient_row[0]

            # Füge die Zutat zur Mahlzeit hinzu (mit Menge)
            cur.execute("""
                INSERT INTO meal_ingredients (meal_id, ingredient_id, amount, unit)
                VALUES (%s, %s, %s, %s)
            """, (meal_id, ingredient_id, amount, unit))

            


            cur.execute("""
    INSERT INTO meal_ingredients (meal_id, ingredient_id, amount, unit)
    VALUES (%s, %s, %s, %s)
""", (meal_id, ingredient_id, amount, unit))


        conn.commit()  # Bestätigt alle Änderungen
        cur.close()
        conn.close()

        return jsonify({"message": "Mahlzeit erfolgreich hinzugefügt!"}), 201

    except Exception as e:
        return jsonify({"error": f"Datenbankfehler: {str(e)}"}), 500

if __name__ == '__main__':
    cors = CORS(app, resources={r"/*": {"origins": "*"}})
    app.run(host='0.0.0.0', port=5000, debug=True)
