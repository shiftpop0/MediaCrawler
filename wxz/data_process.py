import sqlite3
import datetime
from typing import List, Dict, Any, Optional
import os

# --- 配置区 ---


def format_timestamp(ms_timestamp):
    # 将毫秒时间戳转为秒
    ts = int(ms_timestamp) / 1000
    dt = datetime.datetime.fromtimestamp(ts)
    return dt.strftime("%Y年%m月%d日 %H:%M:%S")

def process_notes_and_prepare_data() -> List[Dict[str, str]]:
    DB_PATH = os.path.dirname(os.path.abspath(__file__))+'\\..\\database\\sqlite_tables.db'
    """
    处理笔记和评论数据，并按照指定格式生成用于AI分析的字符串。
    Returns:
        一个列表，每个元素是一个字典，包含格式化后的笔记和评论字符串。
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果可以通过列名访问
    cursor = conn.cursor()

    # 1. 计算半年前的日期
    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
    six_months_ago_ms = int(six_months_ago.timestamp() * 1000)

    # 2. 获取所有笔记
    try:
        cursor.execute("SELECT note_id, liked_count, collected_count, time, last_update_time, title, desc FROM xhs_note WHERE last_update_time >= "+ str(six_months_ago_ms))
        all_notes = cursor.fetchall()
        print(f"成功获取到 {len(all_notes)} 条笔记。")
    except sqlite3.OperationalError as e:
        print(f"错误：无法从'xhs_note'表查询数据。错误信息: {e}")
        conn.close()
        return []

    prepared_data = []

    for note in all_notes:
        note_id = note['note_id']

        # 3. 为每篇笔记提取符合条件的评论
        # 筛选条件：note_id匹配、评论时间在近半年内
        # 排序和限制：按点赞数降序，取前10条
        comment_query = """
            SELECT content, like_count, create_time
            FROM xhs_note_comment
            WHERE note_id = ? AND last_modify_ts >= ?
            ORDER BY like_count DESC
            LIMIT 10
        """
        try:
            cursor.execute(comment_query, (note_id, six_months_ago_ms))
            comments = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"警告：无法为笔记 {note_id} 查询评论。请检查'xhs_note_comment'表和列名。错误信息: {e}")
            comments = [] # 如果查询失败，则评论为空列表

        # 4. 格式化评论字符串
        comment_parts = []
        for i, comment in enumerate(comments, 1):
            comment_str = (
                f"评论{i}："
                # f"点赞数{comment['like_count']}，"
                # f"评论时间{format_timestamp(comment['create_time'])}，"
                f"{comment['content']}"
            )
            comment_parts.append(comment_str)
        
        # 如果没有符合条件的评论，则生成提示信息
        final_comment_string = "\n".join(comment_parts) if comment_parts else "无符合条件的评论（近半年内点赞前10）。"

        # 5. 格式化笔记字符串
        note_string = (
            f"笔记标题：{note['title']}\n"
            # f"点赞数{note['liked_count']}，"
            # f"收藏数{note['collected_count']}，"
            # f"笔记发布时间{format_timestamp(note['time'])}，"
            # f"笔记修改时间{format_timestamp(note['last_update_time'])}，"
            f"笔记内容：{note['desc']}"
        )

        # 6. 存入结果列表
        prepared_data.append({
            "评论": final_comment_string,
            "笔记": note_string,
            "note_id": note_id
        })
    
    conn.close()
    # print("数据库连接已关闭。")
    return prepared_data

def main():
    """
    主函数，执行整个流程
    """
    # 步骤1：处理数据并生成格式化字符串
    all_formatted_data = process_notes_and_prepare_data()

    if not all_formatted_data:
        print("未能处理任何数据，程序退出。")
        return

if __name__ == '__main__':
    main()