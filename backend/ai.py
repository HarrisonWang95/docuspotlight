import os
import base64
import json
import asyncio
from volcenginesdkarkruntime import Ark
from volcengine.visual.VisualService import VisualService
from config import Config
import glob
from dotenv import load_dotenv


# 如果关键环境变量不存在，则加载.env文件
if not os.environ.get("ARK_API_KEY") or not os.environ.get("VOLC_ACCESSKEY"):
    load_dotenv()

# 初始化客户端
client = Ark(
    api_key=os.environ.get("ARK_API_KEY")
)

# 1. 封装的Chat请求函数


def chat_completion(model="deepseek-r1-250120",
                    system_prompt="你是一个专业助手",
                    user_prompt="请50个字介绍一下自己",
                    temperature=0.7,
                    max_tokens=200,
                    output_json=False,
                    json_save_path=Config.EXTRACT_RESULTS_FOLDER):
    """
    封装的聊天完成函数
    doubao-1-5-pro-32k-250115

    参数:
        model: 使用的模型名称
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        temperature: 温度参数
        max_tokens: 最大生成token数
        output_json: 是否尝试解析输出为JSON
        json_save_path: JSON保存路径

    返回:
        如果output_json为True，尝试返回解析后的JSON对象，否则返回原始文本
    """
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )

    response_text = completion.choices[0].message.content

    # 如果需要JSON输出
    if output_json:
        try:
            # 尝试解析JSON内容
            json_content = extract_json_from_text(response_text)
            # 调用文档检索函数

            # 如果提供了保存路径，保存JSON
            if json_save_path:
                os.makedirs(os.path.dirname(json_save_path), exist_ok=True)
                with open(json_save_path, 'w', encoding='utf-8') as f:
                    json.dump(json_content, f, ensure_ascii=False, indent=2)

            return json_content
        except Exception as e:
            print(f"JSON解析错误: {e}")
            return {"error": "无法解析为JSON", "raw_text": response_text}

    return response_text

# 2. 封装的多模态请求函数


def multimodal_completion(file_ids: list,
                          model="doubao-1.5-vision-pro-32k-250115",
                          prompt="描述这些图片的内容",
                          max_tokens=300,
                          output_json=False,
                          json_save_path=None):
    """
    封装的多模态完成函数

    参数:
        file_ids: 图片文件ID列表
        model: 使用的模型名称
        prompt: 提示词
        max_tokens: 最大生成token数
        output_json: 是否尝试解析输出为JSON
        json_save_path: JSON保存路径

    返回:
        如果output_json为True，尝试返回解析后的JSON对象，否则返回原始文本
    """
    # 如果提供了保存路径且文件已存在，直接返回文件内容
    if json_save_path and os.path.exists(json_save_path):
        print(f"使用已有结果: {json_save_path}")
        try:
            with open(json_save_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取已有结果失败: {e}")
            # 如果读取失败，继续执行后续代码重新生成结果
    
    # 存储所有图片的base64数据
    image_contents = []

    # 处理每个文件
    for file_id in file_ids:
        image_path = os.path.join(Config.UPLOAD_FOLDER, file_id)
        if not os.path.exists(image_path):
            print(f"图片路径不存在: {image_path}")
            return None

        # 获取文件扩展名并确定MIME类型
        file_extension = os.path.splitext(file_id)[1].lower()
        mime_type = "image/png"  # 默认MIME类型
        
        # 根据扩展名设置正确的MIME类型
        if file_extension in ['.jpg', '.jpeg']:
            mime_type = "image/jpeg"
        elif file_extension in ['.png', '.apng']:
            mime_type = "image/png"
        elif file_extension == '.gif':
            mime_type = "image/gif"

        # 读取图片并转换为Base64
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{image_data}"
                }
            })

    # 构建请求内容
    content =image_contents+[{"type": "text", "text": prompt}]

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": content
            }
        ],
        max_tokens=max_tokens
    )
    # print(completion)
    response_text = completion.choices[0].message.content

    # 如果需要JSON输出
    if output_json:
        try:
            # 尝试解析JSON内容
            json_content = extract_json_from_text(response_text)
            

            # 如果提供了保存路径，保存JSON
            if json_save_path:
                os.makedirs(os.path.dirname(json_save_path), exist_ok=True)
                with open(json_save_path, 'w', encoding='utf-8') as f:
                    json.dump(json_content, f, ensure_ascii=False, indent=2)
                    # 调用文档检索函数  
                extract_text_locations(task_id)

            return json_content
        except Exception as e:
            print(f"JSON解析错误: {e}, 原始文本: {response_text}")
            return {"error": "无法解析为JSON", "raw_text": response_text}

    return response_text

# 辅助函数：从文本中提取JSON


def extract_json_from_text(text):
    """
    从文本中提取JSON内容
    """
    # 尝试直接解析整个文本
    try:
        return json.loads(text)
    except:
        pass

    # 尝试查找JSON块
    try:
        # 查找可能的JSON块（在```json 和 ``` 之间）
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            return json.loads(json_match.group(1))
    except:
        pass

    # 尝试查找 { 和 } 之间的内容
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
    except:
        pass

    # 如果都失败了，抛出异常
    raise ValueError("无法从文本中提取有效的JSON")

# 3. 文档解析示例 (保持原样)


def document_parse(file_id: str):
    # 初始化服务
    visual_service = VisualService()
    visual_service.set_ak(os.environ.get("VOLC_ACCESSKEY"))
    visual_service.set_sk(os.environ.get("VOLC_SECRETKEY"))
    
    # 构建文件路径
    file_path = os.path.join(Config.UPLOAD_FOLDER, file_id)
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
        
    # 检查是否已有解析结果
    file_extension = os.path.splitext(file_id)[1].lower()
    
    # 处理文件路径，如果没有任务ID则使用根目录
    task_id = file_id.split('/')[0] if '/' in file_id else ''
    filename = file_id.split('/', 1)[1] if '/' in file_id else file_id
    base_name = os.path.splitext(filename)[0]
    # 构建结果目录路径
    result_dir = os.path.join(Config.PARSE_RESULTS_FOLDER, task_id) if task_id else Config.PARSE_RESULTS_FOLDER
    
    # 确保结果目录存在
    os.makedirs(result_dir, exist_ok=True)
    json_path = os.path.join(result_dir, f"{base_name}.json")
    
    # 如果已有解析结果，直接返回
    if os.path.exists(json_path):
        print(f"使用已有解析结果: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 构建请求参数
    form = {
        "image_base64": base64.b64encode(open(file_path, 'rb').read()).decode(),
        "image_url": "",
        "version": "v3",
        "file_type": "pdf" if file_extension == ".pdf" else "image",  
        "page_start": 0,
        "page_num": 1,
        "parse_mode": "auto",
        "table_mode": "markdown",
        "filter_header": "true"
    }

    # 发送请求
    resp = visual_service.ocr_pdf(form)

    if resp.get("data"):

        # 保存 markdown
        markdown_path = os.path.join(result_dir, f"{base_name}.md")
        with open(markdown_path, "w") as f:
            f.write(resp["data"]["markdown"])

        # 保存 JSON
        json_data = json.loads(resp["data"]["detail"])
        json_path = os.path.join(result_dir, f"{base_name}.json")
        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

        print(f"解析结果已保存到: {result_dir}")
        return json_data
    else:
        print("解析请求失败:", resp)
        return None

# 处理多个文件并生成提示词的函数
# 处理多个文件并生成提示词的函数


def process_multiple_files(file_ids: list,
                           model="doubao-1-5-pro-32k-250115",
                           system_prompt="你是一个专业的文档分析助手，擅长从多个文档中提取和整合信息",
                           question="请分析这些文档并提取关键信息",
                           temperature=0.6,
                           max_tokens=500,
                           output_json=False,
                           json_save_path=None):
    """
    处理多个文件并生成提示词，然后调用AI能力

    参数:
        file_ids: 文件ID列表
        model: 使用的模型名称
        system_prompt: 系统提示词
        question: 用户问题
        temperature: 温度参数
        max_tokens: 最大生成token数
        output_json: 是否尝试解析输出为JSON
        json_save_path: JSON保存路径

    返回:
        如果output_json为True，尝试返回解析后的JSON对象，否则返回原始文本
    """
    # 存储所有文件内容
    file_contents = []

    # 处理每个文件
    for file_id in file_ids:
        # 对PDF文件使用文档解析
        if file_id.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.bmp')):
            parsed_data = document_parse(file_id)
            if parsed_data:
                # 将解析结果转为字符串
                file_content = json.dumps(
                    parsed_data, ensure_ascii=False, indent=2)
            else:
                print(f"文件解析失败: {file_id}")
                continue
        else:
            # 对其他文件直接读取内容
            file_path = os.path.join(Config.UPLOAD_FOLDER, file_id)
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            except UnicodeDecodeError:
                # 如果不是文本文件，跳过
                print(f"无法读取文件内容(非文本文件): {file_id}")
                continue

        # 按照模板格式添加文件内容
        file_template = """[file name]: {file_name}
[file content begin]
{file_content}
[file content end]"""

        formatted_content = file_template.format(
            file_name=os.path.basename(file_id),
            file_content=file_content
        )

        file_contents.append(formatted_content)

    # 组合所有文件内容和问题
    combined_prompt = "\n".join(file_contents) + f"\n{question}"

    # 调用chat_completion函数
    return chat_completion(
        model=model,
        system_prompt=system_prompt,
        user_prompt=combined_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        output_json=output_json,
        json_save_path=json_save_path
    )


def extract_text_locations(task_id: str = None, text_to_search: str = None):
    """
    从解析结果中提取文本位置信息

    参数:
        task_id: 任务ID
        text_to_search: 要搜索的文本内容

    返回:
        按照指定格式的JSON对象
    """
    # 如果没有提供task_id，尝试从text_to_search中获取文件路径信息
    if not task_id and text_to_search:
        try:
            # 尝试解析文本中的文件路径信息
            file_info = text_to_search.split('#')
            if len(file_info) >= 2:
                file_path = file_info[0]
                task_id = file_path.split('/')[-2]  # 获取倒数第二个路径部分作为task_id
        except Exception as e:
            print(f"无法从文本中解析task_id: {e}")
            return None

    if not task_id:
        print("未提供task_id且无法从文本中解析")
        return None

    # 构建解析结果文件路径

    parse_result_path = os.path.join(Config.PARSE_RESULTS_FOLDER, task_id, '*.json')
    json_files = glob.glob(parse_result_path)
    if not json_files:
        print(f"解析结果文件不存在: {parse_result_path}")
        return None
    parse_result_path = json_files[0]
    
    # 检查文件是否存在
    if not os.path.exists(parse_result_path):
        print(f"解析结果文件不存在: {parse_result_path}")
        return None

    try:
        # 读取解析结果文件
        with open(parse_result_path, 'r', encoding='utf-8') as f:
            parse_data = json.load(f)

        # 读取markdown_result.json
        extract_result_dir = os.path.join(Config.EXTRACT_RESULTS_FOLDER, task_id)
        os.makedirs(extract_result_dir, exist_ok=True)
        
        # # 列出目录下的所有文件
        # print(f"\n当前目录 {extract_result_dir} 下的文件:")
        # files = glob.glob(os.path.join(extract_result_dir, '*'))
        # for file in files:
        #     print(f"- {os.path.basename(file)}")
        
        markdown_result_path = os.path.join(extract_result_dir, 'markdown_result.json')
        if not os.path.exists(markdown_result_path):
            print(f"markdown_result不存在: {markdown_result_path}")
            return None

        with open(markdown_result_path, 'r', encoding='utf-8') as f:
            markdown_result = json.load(f)

        # 提取文本位置信息
        text_locations = []
        on_the_page = []
        norm_boxes = {}

        # 遍历markdown_result中的所有字段
        for field_name, field_value in markdown_result.items():
            field_value_str = str(field_value)
            # 遍历所有页面的文本块
            for page in parse_data:
                for textblock in page.get('textblocks', []):
                    text = textblock.get('text', '')
                    norm_box = textblock.get('norm_box')
                    
                    # 如果找到匹配的文本
                    if text and norm_box and field_value_str in text:
                        on_the_page.append(field_name)
                        norm_boxes[field_name] = [[norm_box['x0'], norm_box['y0'], norm_box['x1'], norm_box['y1']]]
                        break

        # 构建结果JSON
        result = {
            "onThePage": on_the_page,
            "normBox": norm_boxes
        }

        # 确保结果目录存在
        extract_result_dir = os.path.join(Config.EXTRACT_RESULTS_FOLDER, task_id)
        os.makedirs(extract_result_dir, exist_ok=True)

        # 保存结果
        result_path = os.path.join(extract_result_dir, 'op.json')
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        return result

    except Exception as e:
        print(f"处理文件时出错: {e}")
        return None

    return response_text
if __name__ == '__main__':
    task_id = 'mou'
    # 生成多渠道结果
    result = extract_text_locations(task_id)
    print(result)

    # 测试聊天功能
    # result = chat_completion()
    # print(result)

    #测试多模态功能
    # result = multimodal_completion(
    #     file_ids=["invoice/invoice_test_001_1(0).png", "invoice/invoice_test_001_1(1).png"],
    #     prompt="分析这些发票图片，提取关键信息并以JSON格式返回",
    #      output_json=False
    # )
    # print(result)

    # 测试文档解析
    # document_parse("example.pdf")

    # 测试多文件处理
    # result = process_multiple_files(
    #     file_ids=["example.pdf"],
    #     question="请提取这些文档中的发票信息，并以JSON格式返回",
    #     output_json=True
    # )
    # print(result)
    pass

