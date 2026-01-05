import pandas as pd
from openai import OpenAI
import time
from tqdm import tqdm
import os
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows

# 初始化OpenAI客户端
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
    api_key='887ea839-de56-4d2d-b82d-f7cdfaf1a73e'  # 请替换为有效API Key
)

# 文件路径
input_file = 'input.xlsx'  # 替换为输入文件路径
output_file = 'output.xlsx'  # 输出文件路径
temp_file = 'output_temp.xlsx'  # 临时文件路径

# 检查临时文件是否存在
if os.path.exists(temp_file):
    print(f"发现临时文件 {temp_file}，从中恢复处理进度...")
    # 从临时文件加载已处理的数据
    try:
        df_processed = pd.read_excel(temp_file)
        processed_count = len(df_processed)
        processed_set = set(zip(df_processed['省份'], df_processed['景区']))
        print(f"已从临时文件恢复 {processed_count} 条记录")
    except:
        processed_count = 0
        processed_set = set()
        print("临时文件格式错误，从头开始处理")
else:
    processed_count = 0
    processed_set = set()

# 读取输入数据
try:
    df_input = pd.read_excel(input_file, header=None, names=['省份', '景区'])
    total_rows = len(df_input)
    print(f"成功读取输入文件，共{total_rows}条数据待处理")

    # 创建临时文件（如果不存在）
    if not os.path.exists(temp_file):
        # 创建DataFrame用于临时文件
        df_temp = pd.DataFrame(columns=['省份', '景区', 'API回复'])
        df_temp.to_excel(temp_file, index=False)
        print(f"创建临时文件: {temp_file}")

except Exception as e:
    print(f"读取文件失败: {e}")
    exit()

# 计算剩余待处理数量
remaining_rows = total_rows - processed_count
if remaining_rows <= 0:
    print("所有数据已处理完成！")
    # 重命名临时文件为最终输出文件
    os.rename(temp_file, output_file)
    print(f"结果已保存到: {output_file}")
    exit()

print(f"待处理数据: {remaining_rows}条")

# 创建进度条
progress_bar = tqdm(total=remaining_rows, desc="处理进度", initial=processed_count)

# 加载Excel工作簿
wb = openpyxl.load_workbook(temp_file)
ws = wb.active

# 遍历每一行数据
for index, row in df_input.iterrows():
    province = row['省份']
    attraction = row['景区']

    # 跳过已处理的记录
    if (province, attraction) in processed_set:
        continue

    # 组装用户问题
    user_question = f"{province}省份的{attraction}景点，在2025年8月，是否对公安民警免门票，你的回答稍微简洁明确一些。"

    try:
        # 调用API
        response = client.chat.completions.create(
            model="bot-20250816212613-78clm",  # 替换为你的智能体ID
            messages=[
                {"role": "system", "content": "你是一个旅游信息查询助手，能够准确回答景区门票政策问题"},
                {"role": "user", "content": user_question},
            ],
        )

        # 获取回复内容
        answer = response.choices[0].message.content.strip()
        print(answer)
        is_error = False

    except Exception as e:
        answer = f"错误: {str(e)}"
        is_error = True

    # 添加到已处理集合
    processed_set.add((province, attraction))

    # 添加新行到工作表
    ws.append([province, attraction, answer])

    # 保存到临时文件（每次处理完一条就保存）
    wb.save(temp_file)

    # 更新进度条
    progress_bar.update(1)
    status = f"{province}-{attraction[:10]}" + ("..." if len(attraction) > 10 else "")
    if is_error:
        progress_bar.set_postfix_str(f"错误: {str(e)[:30]}...", refresh=False)
    else:
        progress_bar.set_postfix_str(f"当前: {status}", refresh=False)

    # 避免频繁调用API，适当延迟
    if not is_error:
        time.sleep(1)

# 关闭进度条
progress_bar.close()

# 重命名临时文件为最终输出文件
try:
    wb.save(temp_file)  # 最后保存一次
    os.rename(temp_file, output_file)
    print(f"\n处理完成，结果已保存到: {output_file}")
    print(
        f"成功处理: {len([row for row in ws.iter_rows(min_row=2) if not str(row[2].value).startswith('错误')])}/{total_rows}条")
except Exception as e:
    print(f"\n保存结果文件失败: {e}")
    print(f"临时文件已保存到: {temp_file}")

print("程序结束")