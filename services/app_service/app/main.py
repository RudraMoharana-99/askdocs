from fastapi import FastAPI


app = FastAPI(title="App-services")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}