from openai import OpenAI
import data_process
import sqlite3
import os

# 初步过滤 判断笔记和评论是否与主题相关
def chat1():
    DB_PATH = os.path.dirname(os.path.abspath(__file__))+'\\..\\database\\sqlite_tables.db'
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
        api_key='887ea839-de56-4d2d-b82d-f7cdfaf1a73e'  # 请替换为有效API Key
    )
    note_datas=data_process.process_notes_and_prepare_data()
    for note_data in note_datas:
        # 提前判断以下当前note_id是否在数据库中
        cursor.execute('SELECT 1 FROM xhs_topic_related WHERE note_id=?', (note_data["note_id"],))
        row = cursor.fetchone()
        if row is not None and row[0] is not None:
            continue  # 已存在则跳过
        user_question = "#任务\n 判断以下提供的“笔记”和“评论”内容，是否与主题“警察可以免费进入的旅游景点”相关。请直接回复是与否，不要解释原因或添加任何额外文字。\n\n" \
                        +"#内容如下\n" \
                        +"笔记：\n" + note_data['笔记'] + "\n"\
                        +"评论：\n" + note_data['评论'] + "\n"
        try:
            # 调用API
            response = client.chat.completions.create(
                model="bot-20250816212613-78clm",  # 替换为你的智能体ID
                messages=[
                    {"role": "system", "content": "你是一个内容相关性判断专家"},
                    {"role": "user", "content": user_question},
                ],
                temperature=0.7,
                top_p=0.9,
                # max_tokens=1
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            answer = f"错误: {str(e)}"
        try:
            is_related = 1 if answer[0] == "是" else 0
        except Exception as e:
            continue 
        cursor.execute('''
                INSERT INTO xhs_topic_related (note_id, is_related)
                VALUES (?, ?)
        ''', (note_data["note_id"], is_related))
        conn.commit()

# 深度过滤，对景点免费概率内容打分
def chat2():
    pass

if __name__ == '__main__':
    chat1()
