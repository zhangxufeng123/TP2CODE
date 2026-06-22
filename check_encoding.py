import os

print("开始扫描非 UTF-8 编码的 Python 文件：\n" + "-"*30)
bad_files = []

for root, dirs, files in os.walk("."):
    # 避开虚拟环境文件夹
    if ".venv" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, encoding="utf-8") as f:
                    f.read()
            except UnicodeDecodeError:
                print(f"❌ 发现编码异常的文件: {path}")
                bad_files.append(path)

if not bad_files:
    print("✅ 恭喜，所有文件都是纯净的 UTF-8！")
else:
    print("\n请在 VS Code 中打开上述文件，使用 '通过编码保存' 将其转为 UTF-8。")