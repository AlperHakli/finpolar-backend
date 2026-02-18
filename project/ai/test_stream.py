import requests
import json

url = "http://localhost:8084/analysis/chat"
payload = {
    "message": "merhaba",
    "session_id": "test_alper_123"
}

print(f"Hedef: {url}")
print("İstek gönderiliyor...")

try:
    with requests.post(url, json=payload, stream=True, timeout=30) as response:
        print(f"Sunucu Yanıtı: {response.status_code}")
        print(f"Headers: {response.headers.get('Content-Type')}\n")

        if response.status_code != 200:
            print(f"HATA: Sunucu {response.status_code} döndürdü.")
            print(response.text)
            exit()

        count = 0
        for line in response.iter_lines():
            if line:
                count += 1
                decoded_line = line.decode('utf-8')
                print(f"Token {count}: {decoded_line}")

        if count == 0:
            print("UYARI: Bağlantı başarılı ama sunucudan hiç veri gelmedi (Boş Stream).")

except Exception as e:
    print(f"BAĞLANTI HATASI: {e}")