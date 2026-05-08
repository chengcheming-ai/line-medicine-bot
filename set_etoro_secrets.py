"""
將 .env 裡的 eToro API 金鑰上傳到 GitHub Actions Secrets
"""
import os, subprocess, base64, requests
from nacl import encoding, public
from dotenv import load_dotenv

REPO         = "chengcheming-ai/line-medicine-bot"
SECRET_NAMES = ["ETORO_API_KEY", "ETORO_USER_KEY"]

def get_github_token():
    proc = subprocess.Popen(
        ["git", "credential", "fill"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, _ = proc.communicate(b"protocol=https\nhost=github.com\n\n")
    for line in out.decode().splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    return None

def encrypt_secret(public_key_b64: str, value: str) -> str:
    pk = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder)
    box = public.SealedBox(pk)
    encrypted = box.encrypt(value.encode())
    return base64.b64encode(encrypted).decode()

def set_secret(token, key_id, public_key, name, value):
    encrypted = encrypt_secret(public_key, value)
    resp = requests.put(
        f"https://api.github.com/repos/{REPO}/actions/secrets/{name}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"encrypted_value": encrypted, "key_id": key_id},
    )
    return resp.status_code in (201, 204)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

print("取得 GitHub token...")
token = get_github_token()
if not token:
    print("ERROR: 無法取得 GitHub token，請確認已完成 git push 登入")
    exit(1)

print("取得 repo 公鑰...")
r = requests.get(
    f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
    headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
)
if r.status_code != 200:
    print(f"ERROR: 無法取得公鑰 ({r.status_code}): {r.text}")
    exit(1)

key_id     = r.json()["key_id"]
public_key = r.json()["key"]

for name in SECRET_NAMES:
    value = os.getenv(name)
    if not value:
        print(f"SKIP: {name} 不在 .env，請先填入")
        continue
    ok = set_secret(token, key_id, public_key, name, value)
    print(f"{'OK  ✓' if ok else 'FAIL ✗'}: {name}")

print("\n完成")
