import json

def load_and_standardize(file_path):
    """
    读取原始 JSON 并完成基础校验和标准化。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {e}")
        return []

    standardized = []
    for item in data:
        progress = item.get('progress')
        content = item.get('content')
        
        # 基础校验：过滤缺失 progress、负数 progress、或空内容
        if progress is None or progress < 0 or not content:
            continue
            
        # 标准化提取
        standard_item = {
            "id": str(item.get('id', item.get('id_str', ''))),
            "progress_ms": progress,
            "progress_sec": progress / 1000.0,
            "content": content,
            "mid_hash": item.get('mid_hash', ''),
            "ctime": item.get('ctime', 0)
        }
        standardized.append(standard_item)
        
    return standardized