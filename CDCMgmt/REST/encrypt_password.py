import bcrypt
import json

users = {
    "admin": bcrypt.hashpw("1234".encode(), bcrypt.gensalt()).decode()
}

with open("data/login_credentials.json", "w") as f:
    json.dump(users, f, indent=2)
