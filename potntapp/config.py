import os

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

jwt_secret = os.getenv('JWT_SECRET', 'secret')
image_path = os.getenv('IMAGE_PATH', './images')
