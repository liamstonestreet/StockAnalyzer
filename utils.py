def get_api_key():
    with open("keys.txt", "r") as f:
        return f.read()
    