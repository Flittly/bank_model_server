from flask import Flask
    
def create_app():
    
    app = Flask('Bank Model Service')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
