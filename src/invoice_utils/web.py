from fastapi import FastAPI

app = FastAPI()


@app.post("/invoice")
def generate_invoice():
    return {}
