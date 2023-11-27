import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, People, Planet, User, Favorite  # Importa los modelos desde models.py

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


api = Api(app)


migrate = Migrate(app, db)


CORS(app)

setup_admin(app)

# Inicializa la instancia de db
db.init_app(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


@app.route('/')
def sitemap():
    return generate_sitemap(app)

# perosnas
class PeopleResource(Resource):
    def get(self):
        people_list = People.query.all()
        people_data = [{"id": person.id, "name": person.name} for person in people_list]
        return jsonify({"people": people_data})

class SinglePeopleResource(Resource):
    def get(self, people_id):
        person = People.query.get_or_404(people_id)
        return jsonify({"id": person.id, "name": person.name, "birth_year": person.birth_year, "gender": person.gender})

# las rutas que hice para planets
class PlanetsResource(Resource):
    def get(self):
        planets_list = Planet.query.all()
        planets_data = [{"id": planet.id, "name": planet.name} for planet in planets_list]
        return jsonify({"planets": planets_data})

class SinglePlanetResource(Resource):
    def get(self, planet_id):
        planet = Planet.query.get_or_404(planet_id)
        return jsonify({"id": planet.id, "name": planet.name, "climate": planet.climate, "population": planet.population})


class UsersResource(Resource):
    def get(self):
        users_list = User.query.all()
        users_data = [{"id": user.id, "username": user.username, "email": user.email} for user in users_list]
        return jsonify({"users": users_data})

class SingleUserResource(Resource):
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        user_data = {"id": user.id, "username": user.username, "email": user.email}
        return jsonify(user_data)

class FavoritesResource(Resource):
    def get(self, user_id):
        favorites_list = Favorite.query.filter_by(user_id=user_id).all()
        favorites_data = [{"id": fav.id, "user_id": fav.user_id, "planet_id": fav.planet_id, "people_id": fav.people_id} for fav in favorites_list]
        return jsonify({"favorites": favorites_data})

class AddFavoriteResource(Resource):
    def post(self, user_id, planet_id=None, people_id=None):
        if planet_id is not None:
            # Lógica para añadir un planeta a los favoritos del usuario actual
            favorite = Favorite(user_id=user_id, planet_id=planet_id)
            db.session.add(favorite)
            db.session.commit()
            return jsonify({"message": f"Planet {planet_id} added to favorites for User {user_id}"})
        elif people_id is not None:
            # Lógica para añadir una persona a los favoritos del usuario actual
            favorite = Favorite(user_id=user_id, people_id=people_id)
            db.session.add(favorite)
            db.session.commit()
            return jsonify({"message": f"People {people_id} added to favorites for User {user_id}"})
        else:
            return jsonify({"error": "Invalid request"})

class DeleteFavoriteResource(Resource):
    def delete(self, user_id, planet_id=None, people_id=None):
        if planet_id is not None:
            # Lógica para eliminar un planeta de los favoritos del usuario actual
            favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
            if favorite:
                db.session.delete(favorite)
                db.session.commit()
                return jsonify({"message": f"Planet {planet_id} removed from favorites for User {user_id}"})
            else:
                return jsonify({"error": "Favorite not found"})
        elif people_id is not None:
            # Lógica para eliminar una persona de los favoritos del usuario actual
            favorite = Favorite.query.filter_by(user_id=user_id, people_id=people_id).first()
            if favorite:
                db.session.delete(favorite)
                db.session.commit()
                return jsonify({"message": f"People {people_id} removed from favorites for User {user_id}"})
            else:
                return jsonify({"error": "Favorite not found"})
        else:
            return jsonify({"error": "Invalid request"})


api.add_resource(PeopleResource, '/people')
api.add_resource(SinglePeopleResource, '/people/<int:people_id>')
api.add_resource(PlanetsResource, '/planets')
api.add_resource(SinglePlanetResource, '/planets/<int:planet_id>')
api.add_resource(UsersResource, '/users')
api.add_resource(SingleUserResource, '/users/<int:user_id>')
api.add_resource(FavoritesResource, '/users/<int:user_id>/favorites')
api.add_resource(AddFavoriteResource, '/favorites/user/<int:user_id>/planet/<int:planet_id>', '/favorites/user/<int:user_id>/people/<int:people_id>')
api.add_resource(DeleteFavoriteResource, '/favorites/user/<int:user_id>/planet/<int:planet_id>', '/favorites/user/<int:user_id>/people/<int:people_id>')

# ...

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=3000, debug=True)
