def export_data(episode_id, danmaku_list, series, peaks, stats):
    """
    整理统计结果，输出前端友好的 JSON 结构。
    """
    video_duration_sec = max((d['progress_sec'] for d in danmaku_list), default=0)
    unique_users = len(set(d['mid_hash'] for d in danmaku_list if d.get('mid_hash')))

    # 项目已完全独立，无需再导出兼容 B 站格式的 PBP 数据
    return {
        "episode_id": episode_id,
        "video_duration_sec": video_duration_sec,
        "total_danmaku": len(danmaku_list),
        "unique_users": unique_users,
        "bucket_series": series,
        "peaks": peaks,
        "stats": stats
    }