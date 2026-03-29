import os

base = r"E:\Project Lazarus"
dirs = [
    "frontend",
    "frontend\\src",
    "frontend\\src\\api",
    "frontend\\src\\components",
    "frontend\\src\\types",
    "frontend\\src\\styles",
    "frontend\\public"
]

for d in dirs:
    path = os.path.join(base, d)
    os.makedirs(path, exist_ok=True)
    print(f"Created: {path}")

print("All directories created!")
