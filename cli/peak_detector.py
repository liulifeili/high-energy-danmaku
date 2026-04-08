import statistics

def detect_peaks(series, mode='topn', top_n=10, std_factor=1.5):
    """
    识别每种粒度下的高潮点/峰值区间。
    """
    peaks = {}
    stats = {}

    for g_key, buckets in series.items():
        counts = [b['count'] for b in buckets]
        if not counts:
            peaks[g_key] = []
            stats[g_key] = {"mean": 0, "median": 0, "std": 0, "max": 0}
            continue

        # 计算统计量
        mean_val = statistics.mean(counts)
        median_val = statistics.median(counts)
        std_val = statistics.pstdev(counts) if len(counts) > 1 else 0.0
        max_val = max(counts)

        stats[g_key] = {
            "mean": round(mean_val, 2),
            "median": round(median_val, 2),
            "std": round(std_val, 2),
            "max": max_val
        }

        # 找到峰值桶的索引
        peak_indices = []
        if mode == 'topn':
            sorted_indices = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)
            peak_indices = sorted_indices[:top_n]
        elif mode == 'std':
            threshold = mean_val + std_factor * std_val
            peak_indices = [i for i, c in enumerate(counts) if c > threshold]

        peak_indices = sorted(peak_indices)

        # 合并相邻的高峰桶
        merged_groups = []
        if peak_indices:
            current_group = [peak_indices[0]]
            for i in range(1, len(peak_indices)):
                if peak_indices[i] == current_group[-1] + 1:
                    current_group.append(peak_indices[i])
                else:
                    merged_groups.append(current_group)
                    current_group = [peak_indices[i]]
            merged_groups.append(current_group)

        # 格式化输出高潮区间
        g_peaks = []
        for group in merged_groups:
            group_buckets = [buckets[i] for i in group]
            # 取区间内 count 最大的桶作为绝对峰值点
            peak_bucket = max(group_buckets, key=lambda b: b['count'])
            total_count = sum(b['count'] for b in group_buckets)

            g_peaks.append({
                "start_sec": group_buckets[0]['start_sec'],
                "end_sec": group_buckets[-1]['end_sec'],
                "peak_sec": peak_bucket['mid_sec'],
                "peak_count": peak_bucket['count'],
                "total_count": total_count,
                "relative_strength": round(peak_bucket['count'] / mean_val, 2) if mean_val > 0 else 0,
                "bucket_size": len(group)
            })

        # 按峰值数量倒序排序并赋予排名
        g_peaks.sort(key=lambda x: x['peak_count'], reverse=True)
        # 如果超出 TopN 限制（合并后），重新截断
        if mode == 'topn':
            g_peaks = g_peaks[:top_n]
            
        for i, p in enumerate(g_peaks):
            p['rank'] = i + 1

        peaks[g_key] = g_peaks

    return peaks, stats