"""Quick diagnostic: verifies Groq API connectivity and available models."""
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

key = os.getenv("GROQ_API_KEY")
print(f"GROQ_API_KEY loaded: {'yes' if key else 'NO KEY FOUND'}")

if not key:
    print("Set GROQ_API_KEY in backend/.env and retry.")
    raise SystemExit(1)

client = Groq(api_key=key)

print("\n=== Text model smoke test (llama-3.3-70b-versatile) ===")
try:
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say 'ok'"}],
        max_tokens=5,
    )
    print(f"  OK — response: {r.choices[0].message.content.strip()}")
except Exception as e:
    print(f"  FAILED: {e}")

print("\n=== Vision model smoke test (llama-4-scout-17b-16e-instruct) ===")
try:
    import base64, struct, zlib

    def make_minimal_png() -> bytes:
        def chunk(name: bytes, data: bytes) -> bytes:
            c = name + data
            return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        header = b"\x89PNG\r\n\x1a\n"
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
        iend = chunk(b"IEND", b"")
        return header + ihdr + idat + iend

    b64 = base64.b64encode(make_minimal_png()).decode()
    rv = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this image?"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }],
        max_tokens=20,
    )
    print(f"  OK — response: {rv.choices[0].message.content.strip()[:60]}")
except Exception as e:
    print(f"  FAILED: {e}")

print("\n=== ChromaDB knowledge base status ===")
try:
    import sys
    sys.path.insert(0, ".")
    from rag.retriever import check_collection_exists
    ready = check_collection_exists()
    print(f"  Knowledge base ready: {ready}")
    if not ready:
        print("  Run: python rag/build_kb.py")
except Exception as e:
    print(f"  Could not check KB: {e}")
