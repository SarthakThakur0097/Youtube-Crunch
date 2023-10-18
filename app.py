from flask import Flask
from views import views  # Import the views blueprint

app = Flask(__name__)

# Register the views blueprint
app.register_blueprint(views)

if __name__ == '__main__':
    app.run(debug=True)
