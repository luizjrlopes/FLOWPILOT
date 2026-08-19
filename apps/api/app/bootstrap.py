import uvicorn
from .db import SessionLocal, init_db
from .seed import seed

def main():
    init_db()
    with SessionLocal() as db: seed(db)
    uvicorn.run("app.main:app",host="0.0.0.0",port=8000,reload=False)
if __name__=="__main__": main()
