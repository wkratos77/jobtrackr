import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from config import Config
from extensions import db, login_manager
from routes import auth_bp, jobs_bp
from models import User  
from extensions import db, login_manager, migrate  

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db) 
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(jobs_bp, url_prefix="/jobs")

    @app.get("/")
    def home():
        return "Hello from JobTrackr 👋"

    @app.get("/healthz")
    def healthz():
        return jsonify(ok=True)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

