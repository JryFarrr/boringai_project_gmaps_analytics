from src.app import create_app
from flasgger import Swagger

if __name__ == "__main__":
    app = create_app()
    swagger = Swagger(app)
    app.run(debug=True, host='0.0.0.0', port=5000)