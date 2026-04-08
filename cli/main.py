import json
import os
import glob
from loader import load_and_standardize
from aggregator import aggregate_danmaku
from peak_detector import detect_peaks
from exporter import export_data

def process_file(input_file, episode_id, output_dir, top_n, peak_mode, std_factor):
    print(f"[*] 处理文件: {input_file} (集数: {episode_id})")
    standardized = load_and_standardize(input_file)
    if not standardized:
        print("  [-] 警告: 未读取到有效弹幕。")
        return None
        
    print(f"  [+] 读取有效弹幕 {len(standardized)} 条。")

    # 【核心修复】：彻底移除 '100等分'，只保留 '增强分析' 和纯数字粒度
    granularities = [5, 10, 30, 60, 300, '增强分析']
    series = aggregate_danmaku(standardized, granularities)
    peaks, stats = detect_peaks(series, mode=peak_mode, top_n=top_n, std_factor=std_factor)
    output_data = export_data(episode_id, standardized, series, peaks, stats)

    # 依然保留单个 json 文件的输出，方便查阅
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{episode_id}.json")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"  [+] 成功导出单集分析结果至: {output_file}")
    return output_data

def main():
    # 获取当前 main.py 脚本所在的绝对物理目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 自动推断项目根目录：如果脚本在 'cli' 文件夹内，则根目录为其上一级
    if os.path.basename(script_dir) == 'cli':
        project_root = os.path.dirname(script_dir)
    else:
        project_root = script_dir

    # 动态拼接绝对路径，彻底解决不同终端路径下执行报错的问题
    input_dir = os.path.join(project_root, "data", "raw")
    output_dir = os.path.join(project_root, "data", "processed")
    
    top_n = 10
    peak_mode = "topn"
    std_factor = 1.5

    # 1. 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"\n[!] 错误: 找不到输入目录 '{input_dir}'")
        print("    请确保在正确的目录下创建了 data/raw 文件夹，或者检查项目结构。")
        return

    print(f"[*] 项目根目录定位: {project_root}")
    print(f"[*] 数据输入目录: {input_dir}")
    print(f"[*] 数据输出目录: {output_dir}")
    print("-" * 55)

    # 2. 获取所有 JSON 文件
    files = glob.glob(os.path.join(input_dir, "*.json"))
    
    if not files:
        print(f"\n[!] 警告: 目录 '{input_dir}' 中没有找到任何 JSON 文件。")
        print("    请先将弹幕 JSON 数据放进去。")
        return

    print(f"[*] 发现 {len(files)} 个待处理文件，开始分析...\n")

    # 用于聚合所有集数的数据字典
    all_episodes_data = {}

    # 3. 批量执行分析并收集结果
    for file in files:
        episode_id = os.path.splitext(os.path.basename(file))[0]
        result = process_file(file, episode_id, output_dir, top_n, peak_mode, std_factor)
        if result:
            all_episodes_data[episode_id] = result

    # 4. 自动生成 JS 数据文件，整合所有剧集供前端一键加载和切换
    js_output_file = os.path.join(output_dir, "data.js")
    with open(js_output_file, 'w', encoding='utf-8') as f:
        f.write("window.APP_DATA = ")
        json.dump(all_episodes_data, f, ensure_ascii=False, indent=2)
        f.write(";\n")
        
    print(f"\n[*] 恭喜！处理完毕。共包含 {len(all_episodes_data)} 集数据。")
    print(f"[*] 前端所需多集整合数据文件已生成至: {js_output_file}")
    print(f"[*] 请直接用浏览器打开 index.html 即可在左侧边栏无缝切换各集分析视图！")

if __name__ == "__main__":
    main()