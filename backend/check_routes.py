import asyncio
from app.main import fastapi_app

def print_routes():
    for route in fastapi_app.routes:
        print(f"{route.path} {route.methods}")

if __name__ == "__main__":
    print_routes()
