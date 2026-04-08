import math

def aggregate_danmaku(danmaku_list, granularities=[5, 10, 30, 60, 300, '增强分析']):
    """
    按指定的时间粒度统计弹幕数量。
    '增强分析' 模式：自研算法。平衡 5s 的尖锐度与 100等分的平滑度，采用多尺度感知锐化算法。
    """
    if not danmaku_list:
        return {
            ("1min" if g == 60 else "5min" if g == 300 else f"{g}s" if isinstance(g, int) else g): [] 
            for g in granularities
        }

    max_sec = max(d['progress_sec'] for d in danmaku_list)
    series = {}
    
    for g in granularities:
        if g == '增强分析':
            # 基于视频总时长计算等分步长，始终将全片切分为 100 份
            step_sec = max(1, math.ceil(max_sec / 100.0))
            bucket_count = 100
            g_key = g
        else:
            bucket_count = math.ceil(max_sec / g) if max_sec > 0 else 1
            step_sec = float(g)
            g_key = "1min" if g == 60 else "5min" if g == 300 else f"{g}s"
            
        buckets = []
        for i in range(bucket_count):
            buckets.append({
                "start_sec": i * step_sec,
                "end_sec": (i + 1) * step_sec,
                "mid_sec": i * step_sec + step_sec / 2.0,
                "count": 0
            })
            
        for d in danmaku_list:
            idx = int(d['progress_sec'] // step_sec)
            if 0 <= idx < bucket_count:
                buckets[idx]['count'] += 1

        # 【核心算法：多尺度感知锐化】
        if g_key == '增强分析' and bucket_count > 0:
            # 1. 预计算 5s 粒度的微观数据作为参考
            micro_step = 5.0
            micro_count = math.ceil(max_sec / micro_step)
            micro_raw = [0] * micro_count
            for d in danmaku_list:
                m_idx = int(d['progress_sec'] // micro_step)
                if m_idx < micro_count: micro_raw[m_idx] += 1

            processed_counts = []
            for i in range(bucket_count):
                curr_bucket = buckets[i]
                # 提取落入当前大桶内的所有 5s 小桶
                m_start = int(curr_bucket['start_sec'] // micro_step)
                m_end = int(curr_bucket['end_sec'] // micro_step)
                sub_samples = micro_raw[m_start:m_end+1]
                
                # 计算微观特征：不仅看总量，看最大瞬时爆发点
                max_micro = max(sub_samples) if sub_samples else 0
                avg_micro = sum(sub_samples) / len(sub_samples) if sub_samples else 1
                
                # 爆发比率：如果瞬时最大值远超平均值，说明这里有“尖刺”
                burst_factor = (max_micro / avg_micro) if avg_micro > 0 else 1.0
                
                # 组合得分：宏观总量 * (微观爆发比的增强)
                score = curr_bucket['count'] * (burst_factor ** 1.2)
                processed_counts.append(score)

            # 2. 局部对比度拉伸：剔除底噪，拉开差距
            min_v = min(processed_counts)
            normalized = [max(0, v - min_v) for v in processed_counts]
            
            # 3. 最终平滑与锐化平衡
            final_counts = []
            for i in range(bucket_count):
                p = normalized[i-1] if i > 0 else normalized[i]
                n = normalized[i+1] if i < bucket_count - 1 else normalized[i]
                c = normalized[i]
                # 1:4:1 中心加权平滑，去生硬折角保陡峭
                smooth_v = (p + 4*c + n) / 6.0
                final_counts.append(smooth_v)
            
            # 4. 非线性动态阈值拉伸
            max_final = max(final_counts) if max(final_counts) > 0 else 1
            for i in range(bucket_count):
                # 1.8 次幂压制水弹幕底噪，突显高能针刺
                val = (final_counts[i] / max_final) ** 1.8 * max_final
                buckets[i]['count'] = round(val, 1)
            
        series[g_key] = buckets

    return series