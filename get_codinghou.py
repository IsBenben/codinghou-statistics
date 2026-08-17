import requests
import sys
import os
import re
import zipfile
import io
import time
import json
from config import TOKEN, LIST_URL, DETAIL_URL, OUTPUT_DIR, PAGE_SIZE, PROGRESS_FILE, START_PAGE, REQUEST_INTERVAL

def sanitize_filename(name: str) -> str:
    illegal_chars = r'[\\/:*?"<>|]'
    return re.sub(illegal_chars, ' ', name).strip()

def decrypt_sb3(data: bytes) -> bytes:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return data
    except zipfile.BadZipFile:
        pass

    decrypted = bytes([b ^ 0xFF for b in data])

    def to_signed(byte_val: int) -> int:
        return byte_val if byte_val < 128 else byte_val - 256

    header = [to_signed(b) for b in decrypted[:9]]
    pattern1 = [3, 15, 4, 9, 14, 7, 8, 15, 21]
    pattern2 = [-4, -16, -5, -10, -15, -8, -9, -16, -22]

    if header == pattern1 or header == pattern2:
        decrypted = decrypted[9:]
        print("检测到混淆头部，已移除。")
    else:
        print("未检测到已知头部，保持取反后的数据。")

    return decrypted

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('page', START_PAGE), data.get('index', 0)
        except:
            pass
    return START_PAGE, 0

def save_progress(page, index):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'page': page, 'index': index}, f)

def clear_progress():
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

def download_and_decrypt(work_id: int, name: str, token: str) -> bool:
    """
    下载并解密单个作品。
    如果目标文件已存在（基于 work_id 唯一命名），则跳过下载并返回 True。
    """
    # ---------- 新增：检查文件是否已存在 ----------
    safe_name = sanitize_filename(name)
    if not safe_name:
        safe_name = "untitled"
    # 文件名包含作品ID，保证唯一性
    output_path = os.path.join(OUTPUT_DIR, f"{work_id} {safe_name}.sb3")
    if os.path.exists(output_path):
        print(f"  文件已存在，跳过: {output_path}")
        return True  # 视为成功，进度后移
    # -------------------------------------------

    try:
        # 1. 获取详情
        detail_headers = {"Token": token}
        detail_payload = {"id": work_id}
        resp = requests.post(DETAIL_URL, json=detail_payload, headers=detail_headers)
        resp.raise_for_status()
        result = resp.json()
        data_obj = result.get("data", {})
        file_url = data_obj.get("fileUrl")
        if not file_url:
            print(f"  作品 {work_id} 无 fileUrl，跳过")
            return False

        print(f"  开始下载: {name} (ID: {work_id})")
        # 2. 流式下载
        download_headers = {"Token": token}
        with requests.get(file_url, headers=download_headers, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            chunk_size = 1024 * 32
            downloaded = 0
            raw_data = bytearray()
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    raw_data.extend(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        sys.stdout.write(f"\r  下载进度: {percent:.2f}% ({downloaded}/{total_size} 字节)")
                        sys.stdout.flush()
            print()

        # 3. 解密
        decrypted_data = decrypt_sb3(bytes(raw_data))

        # 4. 保存（此时路径已在上方确定，无需重复生成）
        with open(output_path, "wb") as f:
            f.write(decrypted_data)
        print(f"  解密完成，已保存至: {output_path}")
        return True

    except Exception as e:
        print(f"  处理作品 {work_id} 时出错: {e}")
        return False

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    page, index = load_progress()
    print(f"从第 {page} 页，第 {index+1} 个作品开始继续...")

    list_headers = {"Token": TOKEN}
    list_payload = {
        "order": "favorsCount",
        "keyWord": "",
        "page": page,
        "size": PAGE_SIZE,
        "responseMode": "card"
    }

    try:
        while True:
            list_payload["page"] = page
            resp = requests.post(LIST_URL, json=list_payload, headers=list_headers)
            resp.raise_for_status()
            result = resp.json()
            data_list = result.get("data", {}).get("list", [])

            if not data_list:
                print(f"第 {page} 页无数据，全部处理完成。")
                clear_progress()
                break

            print(f"\n--- 第 {page} 页，共 {len(data_list)} 个作品 ---")
            for i in range(index, len(data_list)):
                item = data_list[i]
                work_id = item.get("id")
                name = item.get("name", f"未命名_{work_id}")
                print(f"[{i+1}/{len(data_list)}] 处理作品: {name} (ID: {work_id})")
                success = download_and_decrypt(work_id, name, TOKEN)
                # 无论成功或跳过，都更新索引到下一个
                new_index = i + 1
                save_progress(page, new_index)
                print()
                time.sleep(REQUEST_INTERVAL)

            # 该页全部处理完毕，进入下一页
            page += 1
            index = 0
            save_progress(page, index)

            if len(data_list) < PAGE_SIZE:
                print("已到达最后一页，全部处理完成。")
                clear_progress()
                break

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"JSON 解析失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
