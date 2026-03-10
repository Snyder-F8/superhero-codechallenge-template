#!/usr/bin/env python3

from flask import Flask, request, make_response, jsonify
from flask_migrate import Migrate
from models import db, Hero, Power, HeroPower
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)


@app.route("/")
def index():
    return "<h1>Superheroes API</h1>"



# GET /heroes

@app.route("/heroes", methods=["GET"])
def get_heroes():
    heroes = Hero.query.all()
    heroes_list = [
        hero.to_dict(only=("id", "name", "super_name"))
        for hero in heroes
    ]
    return make_response(jsonify(heroes_list), 200)



# GET /heroes/<id>

@app.route("/heroes/<int:id>", methods=["GET"])
def get_hero_by_id(id):
    hero = Hero.query.filter(Hero.id == id).first()
    if not hero:
        return make_response(jsonify({"error": "Hero not found"}), 404)
    # Include hero_powers but prevent recursion
    hero_dict = hero.to_dict(rules=("-hero_powers.hero",))
    return make_response(jsonify(hero_dict), 200)


# GET /powers

@app.route("/powers", methods=["GET"])
def get_powers():
    powers = Power.query.all()
    # Only include id, name, description (no hero_powers)
    powers_list = [power.to_dict(only=("id", "name", "description")) for power in powers]
    return make_response(jsonify(powers_list), 200)



# GET /powers/<id>
@app.route("/powers/<int:id>", methods=["GET"])
def get_power_by_id(id):
    power = Power.query.filter(Power.id == id).first()
    if not power:
        return make_response(jsonify({"error": "Power not found"}), 404)
    # Only include id, name, description (no hero_powers)
    return make_response(jsonify(power.to_dict(only=("id", "name", "description"))), 200)


# PATCH /powers/<id>

@app.route("/powers/<int:id>", methods=["PATCH"])
def update_power(id):
    power = Power.query.filter(Power.id == id).first()
    if not power:
        return make_response(jsonify({"error": "Power not found"}), 404)

    data = request.get_json()

    try:
        power.description = data["description"]
        db.session.commit()
        return make_response(
            jsonify(power.to_dict(only=("id", "name", "description"))),
            200
        )
    except Exception:
        return make_response(jsonify({"errors": ["validation errors"]}), 400)


# POST /hero_powers
@app.route("/hero_powers", methods=["POST"])
def create_hero_power():
    data = request.get_json()
    try:
        new_hero_power = HeroPower(
            strength=data["strength"],
            hero_id=data["hero_id"],
            power_id=data["power_id"],
        )
        db.session.add(new_hero_power)
        db.session.commit()

        # Include hero and power but avoid recursive hero_powers in response
        response = new_hero_power.to_dict(
            rules=(
                "-hero.hero_powers",
                "-power.hero_powers",
            )
        )
        return make_response(jsonify(response), 200)
    except Exception as e:
        return make_response(jsonify({"errors": ["validation errors"]}), 400)


if __name__ == "__main__":
    app.run(port=5555, debug=True)