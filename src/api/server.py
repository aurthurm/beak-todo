"""Entry point: beak-flow"""


def main():
    import uvicorn

    uvicorn.run("src.api.app:app", host="127.0.0.1", port=8787, reload=False)
