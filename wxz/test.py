import sqlite3
import datetime
from typing import List, Dict, Any, Optional

# --- 配置区 ---
DB_PATH = './test/sqlite_tables.db'

def format_timestamp(ms_timestamp):
    # 将毫秒时间戳转为秒
    ts = int(ms_timestamp) / 1000
    dt = datetime.datetime.fromtimestamp(ts)
    return dt.strftime("%Y年%m月%d日 %H:%M:%S")

def call_ai_model(text_to_analyze: str) -> bool:
    """
    模拟调用AI模型的函数。
    你需要在这里替换为与你的AI服务进行交互的真实代码。
    
    Args:
        text_to_analyze: 拼接后的笔记和评论内容字符串。

    Returns:
        一个布尔值，表示AI模型判断该文本是否讨论免票政策。
    """
    print("--- 准备发送给AI模型进行分析 ---")
    # 为了可读性，只打印前300个字符
    print(f"待分析内容 (前300字符): \n{text_to_analyze[:300]}...\n") 
    
    # 【重要】 在此处替换为你的真实AI API调用逻辑
    # 例如:
    # headers = {"Authorization": "Bearer YOUR_API_KEY"}
    # data = {"model": "your_model_name", "prompt": text_to_analyze}
    # response = requests.post("https://api.example.com/v1/completions", json=data, headers=headers)
    # result = response.json()
    # is_policy_related = "免票政策" in result['choices'][0]['text'] 
    
    # 以下为模拟返回，我们假设如果文本中包含“免票”或“工作证”，则认为相关
    is_policy_related = "免票" in text_to_analyze or "工作证" in text_to_analyze
    
    print(f"AI分析结果: {'是免票政策相关笔记' if is_policy_related else '非免票政策相关笔记'}")
    print("-" * 30)
    
    return is_policy_related

def process_notes_and_prepare_data(db_path: str) -> List[Dict[str, str]]:
    """
    处理笔记和评论数据，并按照指定格式生成用于AI分析的字符串。
    Returns:
        一个列表，每个元素是一个字典，包含格式化后的笔记和评论字符串。
    """
    print(f"正在连接数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 让查询结果可以通过列名访问
    cursor = conn.cursor()

    # 1. 计算半年前的日期
    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=1)
    # 将其格式化为与数据库中时间戳匹配的字符串格式 (假设为 'YYYY-MM-DD HH:MM:SS')
    # six_months_ago_str = six_months_ago.strftime('%Y-%m-%d %H:%M:%S')
    six_months_ago_ms = int(six_months_ago.timestamp() * 1000)

    # 2. 获取所有笔记
    try:
        cursor.execute("SELECT note_id, liked_count, collected_count, time, last_update_time, title, desc FROM xhs_note")
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
            WHERE note_id = ? AND time >= ?
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
                f"评论{i}：点赞数{comment['like_count']}，"
                f"评论时间{comment['create_time']}，"
                f"{comment['content']}"
            )
            comment_parts.append(comment_str)
        
        # 如果没有符合条件的评论，则生成提示信息
        final_comment_string = "\n".join(comment_parts) if comment_parts else "无符合条件的评论（近半年内点赞前10）。"

        # 5. 格式化笔记字符串
        note_string = (
            f"点赞数{note['liked_count']}，"
            f"收藏数{note['collected_count']}，"
            f"笔记发布时间{note['time']}，"
            f"笔记修改时间{note['last_update_time']}，"
            f"笔记标题{note['title']}，"
            f"{note['desc']}"
        )

        # 6. 存入结果列表
        prepared_data.append({
            "note_id": note_id,
            "formatted_note": note_string,
            "formatted_comments": final_comment_string,
        })
    
    conn.close()
    print("数据库连接已关闭。")
    return prepared_data

def main():
    """
    主函数，执行整个流程
    """
    # 步骤1：处理数据并生成格式化字符串
    all_formatted_data = process_notes_and_prepare_data(DB_PATH)

    if not all_formatted_data:
        print("未能处理任何数据，程序退出。")
        return

    # print(f"\n已为 {len(all_formatted_data)} 条笔记准备好数据，即将开始调用AI模型分析...")

    # policy_related_notes = []

    # # 步骤2：遍历数据，拼接并调用AI模型
    # for data_item in all_formatted_data:
    #     # 拼接笔记和评论字符串
    #     full_text = f"笔记内容：\n{data_item['formatted_note']}\n\n相关评论：\n{data_item['formatted_comments']}"
        
    #     # 调用AI进行判断
    #     is_related = call_ai_model(full_text)
        
    #     if is_related:
    #         policy_related_notes.append(data_item['note_id'])

    # print("\n--- 分析完成 ---")
    # print(f"共有 {len(policy_related_notes)} 篇笔记被AI识别为免票政策相关。")
    # if policy_related_notes:
    #     print("这些笔记的ID是:", policy_related_notes)
    #     print("下一步，你可以根据这些ID去爬取更多评论。")

if __name__ == '__main__':
    main()