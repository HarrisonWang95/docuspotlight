from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import glob
import uuid
import asyncio
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config  # 添加这行
import ai  # 导入AI模块
from concurrent.futures import ThreadPoolExecutor  # 添加这行

app = Flask(__name__)
app.config.from_object(Config)  # 使用配置类

# CORS配置，允许所有API路由的跨域访问
frontend_port = os.environ.get('FRONTEND_PORT', '32211')
frontend_origins = [f'http://localhost:{frontend_port}', f'http://127.0.0.1:{frontend_port}']
CORS(app, resources={
    r"/*": {
        "origins": frontend_origins,  # 从环境变量读取允许的域名列表
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# 配置文件上传目录
# 删除以下硬编码配置
# UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
# ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 修改为使用配置类的属性
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 解析结果存储目录
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# 多渠道解析结果存储目录
EXTRACT_RESULTS_FOLDER = Config.EXTRACT_RESULTS_FOLDER
os.makedirs(EXTRACT_RESULTS_FOLDER, exist_ok=True)

# Schema存储目录
SCHEMA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema')
os.makedirs(SCHEMA_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 获取任务ID，如果没有提供则创建一个新的
    task_id = request.form.get('task_id')
    if not task_id:
        task_id = f"task_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
    
    # 确保任务目录存在
    task_folder = os.path.join(app.config['UPLOAD_FOLDER'], task_id)
    os.makedirs(task_folder, exist_ok=True)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(task_folder, filename)
        file.save(file_path)
        
        # 这里可以调用文档解析服务
        # 模拟解析结果
        parse_result = {
            'document_id': filename,
            'task_id': task_id,
            'items': [
                {
                    'id': 1,
                    'type': '基本信息',
                    'fields': [
                        {'name': '姓名', 'value': '张三', 'confidence': 0.95},
                        {'name': '日期', 'value': '2023-05-15', 'confidence': 0.92}
                    ]
                },
                {
                    'id': 2,
                    'type': '核心条款',
                    'fields': [
                        {'name': '合同金额', 'value': '100,000元', 'confidence': 0.88},
                        {'name': '签署日期', 'value': '2023-05-20', 'confidence': 0.90}
                    ]
                }
            ]
        }
        
        # 保存解析结果
        result_path = os.path.join(RESULTS_FOLDER, f"{task_id}_{filename.rsplit('.', 1)[0]}.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(parse_result, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'message': '文件上传成功',
            'filename': filename,
            'task_id': task_id,
            'chucking_result': parse_result
        })
    
    return jsonify({'error': '不允许的文件类型'}), 400

@app.route('/api/files/<path:file_path>', methods=['GET'])
def get_file(file_path):
    # 分离任务ID和文件名
    parts = file_path.split('/')
    if len(parts) >= 2:
        task_id = parts[0]
        filename = '/'.join(parts[1:])
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], task_id), filename)
    else:
        return send_from_directory(app.config['UPLOAD_FOLDER'], file_path)

@app.route('/api/results/<document_id>', methods=['GET'])
def get_result(document_id):
    # 移除可能的文件扩展名
    base_name = document_id.rsplit('.', 1)[0]
    result_path = os.path.join(RESULTS_FOLDER, f"{base_name}.json")
    
    if os.path.exists(result_path):
        with open(result_path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    else:
        return jsonify({'error': '找不到解析结果'}), 404

@app.route('/api/verify', methods=['POST'])
def verify_result():
    data = request.json
    document_id = data.get('document_id')
    verified_items = data.get('verified_items', [])
    
    # 保存验证结果
    verification_path = os.path.join(RESULTS_FOLDER, f"{document_id.rsplit('.', 1)[0]}_verified.json")
    with open(verification_path, 'w', encoding='utf-8') as f:
        json.dump(verified_items, f, ensure_ascii=False, indent=2)
    
    return jsonify({'message': '验证结果已保存'})

# API端点

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """获取所有已上传的文档列表"""
    documents = []
    for filename in os.listdir(UPLOAD_FOLDER):
        print(filename)
        if allowed_file(filename):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            documents.append({
                'id': filename,
                'name': filename,
                'upload_time': os.path.getmtime(file_path),
                'size': os.path.getsize(file_path)
            })
    
    # 按上传时间排序，最新的在前
    documents.sort(key=lambda x: x['upload_time'], reverse=True)
    return jsonify(documents)

@app.route('/api/documents/<path:task_id>', methods=['GET'])
def get_document(task_id):
    """获取指定文档及其相关文件的详细信息"""
    # 构建目标文件夹路径
    target_folder = os.path.join(UPLOAD_FOLDER, task_id)
    
    # 检查路径是否存在
    if not os.path.exists(target_folder):
        return jsonify({'error': '路径不存在'}), 404
    
    # 查找所有相关文件
    documents = []
    for filename in os.listdir(target_folder):
        if allowed_file(filename):
            file_path = os.path.join(target_folder, filename)
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            file_type = 'application/pdf' if file_extension == 'pdf' else f'image/{file_extension}'
            
            documents.append({
                'id': os.path.join(task_id, filename),  # 包含相对路径的文件ID
                'filename': filename,
                'file_type': file_type,
                'upload_time': os.path.getmtime(file_path),
                'size': os.path.getsize(file_path)
            })
    
    if not documents:
        return jsonify({'error': '文件夹中没有符合要求的文件'}), 404
        
    return jsonify({
        'documents': documents
    })

@app.route('/api/create-task', methods=['POST'])
def create_task():
    """创建新的任务ID"""
    # 生成唯一的任务ID
    task_id = f"task_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
    
    # 创建任务文件夹
    task_folder = os.path.join(app.config['UPLOAD_FOLDER'], task_id)
    os.makedirs(task_folder, exist_ok=True)
    
    # 返回任务ID
    return jsonify({
        'task_id': task_id
    })

@app.route('/api/schema/<task_id>', methods=['GET'])
def get_schema_with_taskid(task_id):
    """获取指定任务的JSON Schema"""
    schema_path = os.path.join(SCHEMA_FOLDER, f"{task_id}.json")
    
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    else:
        # 如果没有找到特定任务的Schema，返回默认Schema
        default_schema_path = os.path.join(SCHEMA_FOLDER, "invoice_A2P.json")
        if os.path.exists(default_schema_path):
            with open(default_schema_path, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        else:
            # 如果连默认Schema都没有，返回一个基本结构
            default_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "文档解析Schema",
                "type": "object",
                "properties": {
                    "invoiceNumber": {
                        "type": "string",
                        "title": "发票号码",
                        "description": "发票唯一标识号码"
                    },
                    "invoiceDate": {
                        "type": "string",
                        "format": "date",
                        "title": "发票日期",
                        "description": "发票开具日期"
                    }
                },
                "required": ["invoiceNumber", "invoiceDate"]
            }
            return jsonify(default_schema)

# 添加异步处理函数
async def process_with_ai(task_id, schema_data,extract_strategy=["markdown","multi-modal"],):
    """
    使用AI处理任务
    
    参数:
        task_id: 任务ID
        schema_data: Schema数据
    """
    try:
        # 从schema中提取提示词，如果没有则使用默认值
        system_prompt = schema_data.get('system_prompt', '你是一个专业的文档分析助手，擅长从文档中提取结构化信息')
        user_prompt = schema_data.get('user_prompt', '请分析这个文档并提取关键信息,并以JSON格式返回，jsonSchema如下：{jsonSchema}')
        user_prompt = user_prompt.format(jsonSchema=json.dumps(schema_data, ensure_ascii=False))
        # print(user_prompt)
        # 获取任务相关的文件
        task_folder = os.path.join(UPLOAD_FOLDER, task_id)
        if not os.path.exists(task_folder):
            print(f"任务文件夹不存在: {task_folder}")
            return
        
        # 查找所有相关文件
        files = []
        for filename in os.listdir(task_folder):
            if allowed_file(filename):
                files.append(os.path.join(task_id, filename))
        
        if not files:
            print(f"任务 {task_id} 没有可处理的文件")
            return
        
        # 确保结果目录存在
        extract_result_folder = os.path.join(EXTRACT_RESULTS_FOLDER, task_id)
        os.makedirs(extract_result_folder, exist_ok=True)


        # 根据文件扩展名过滤文件列表
        multimodal_files = [file_id for file_id in files if '.' in file_id and file_id.rsplit('.', 1)[1].lower() in Config.MULTIMODAL_ALLOWED_EXTENSIONS]
        markdown_files = [file_id for file_id in files if '.' in file_id and file_id.rsplit('.', 1)[1].lower() in Config.MARKDOWN_ALLOWED_EXTENSIONS]
        try:
            # 处理多模态文件
            if multimodal_files and "multi-modal" in extract_strategy:
                print(f"正在处理多模态文件: {multimodal_files}")
                # 图像文件使用多模态处理
                result = ai.multimodal_completion(
                    file_ids=multimodal_files,
                    prompt=user_prompt,
                    output_json=True,
                    json_save_path=os.path.join(extract_result_folder, f"multimodal_result.json")
                )
                print(f"多模态处理完成: {multimodal_files}")
        except Exception as e:
            print(f"多模态处理出错: {e}")
        try:
            # 处理需要markdown解析的文件
            if markdown_files and "markdown" in extract_strategy:
                print(f"正在处理PDF文件: {markdown_files}")
                # 使用process_multiple_files处理PDF文件
                result = ai.process_multiple_files(
                    file_ids=markdown_files,
                    system_prompt=system_prompt,
                    question=user_prompt,
                    output_json=True,
                    json_save_path=os.path.join(extract_result_folder, f"markdown_result.json")
                )
                print(f"PDF处理完成: {markdown_files}")
        except Exception as e:
            print(f"PDF处理出错: {e}")
            
            print(f"任务 {task_id} 处理完成")
        
    except Exception as e:
        print(f"AI处理出错: {e}")

# 创建线程池执行器
executor = ThreadPoolExecutor(max_workers=4)  # 可以根据需要调整线程数

@app.route('/api/schema/<task_id>', methods=['POST'])
def save_schema(task_id):
    """保存指定任务的JSON Schema并触发AI处理"""
    schema_data = request.json
    
    if not schema_data:
        return jsonify({'error': '无效的Schema数据'}), 400
    
    # 确保Schema目录存在
    os.makedirs(SCHEMA_FOLDER, exist_ok=True)
    
    # 保存Schema
    schema_path = os.path.join(SCHEMA_FOLDER, f"{task_id}.json")
    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(schema_data, f, ensure_ascii=False, indent=2)
    
    # 使用线程池执行器替代asyncio.run
    # 创建一个同步包装函数来调用异步函数
    def run_async_task(task_id, schema_data):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(process_with_ai(task_id, schema_data))
        finally:
            loop.close()
    
    # 提交任务到线程池并获取Future对象
    future = executor.submit(run_async_task, task_id, schema_data)
    
    # 等待任务完成
    future.result()
    return jsonify({
        'message': 'Schema保存成功，AI处理已完成',
        'task_id': task_id
    })

@app.route('/api/multi-channel-results/<task_id>', methods=['GET'])
def get_multi_channel_results(task_id):
    """获取多渠道解析结果"""
    # 获取所有渠道的解析结果
    field_name_map={"markdown_result":"DeepSeek-R1","multimodal_result":"豆包vision"}
    channels = []
    on_the_page=[]
    norm_box=[]
    channel_files = glob.glob(os.path.join(EXTRACT_RESULTS_FOLDER, f"{task_id}/*.json"))
    
    
    # 如果没有找到特定文档的渠道文件，则使用所有可用的渠道文件
    if not channel_files:
        channel_files = glob.glob(os.path.join(EXTRACT_RESULTS_FOLDER, "invoice/*.json"))
    
    for file_path in channel_files:
        channel_name = os.path.splitext(os.path.basename(file_path))[0]  # 提取不带扩展名的文件名
        if(channel_name != "op"):  # 修改判断条件
            print(channel_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                channel_data = json.load(f)
                channels.append({
                    "channel": field_name_map.get(channel_name, channel_name),
                    "data": channel_data
                })
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                op_data = json.load(f)
                on_the_page = op_data["onThePage"]
                norm_box=op_data["normBox"]
    # 生成默认的人类人工核对结果（使用第一个渠道的结果作为默认值）
    default_decision = {}
    if channels:
        default_decision = channels[0]["data"]
    
    return jsonify({
        "channels": channels,
        "onThePage": on_the_page,
        "normBox": norm_box,
        "defaultDecision": default_decision
        

    })

@app.route('/api/schema/<schema_name>', methods=['GET'])
def get_schema(schema_name):
    """获取指定的JSON Schema"""
    schema_path = os.path.join(SCHEMA_FOLDER, f"{schema_name}.json")
    
    if not os.path.exists(schema_path):
        return jsonify({'error': '找不到指定的Schema'}), 404
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_data = json.load(f)
    
    return jsonify(schema_data)

@app.route('/api/save-decision', methods=['POST'])
def save_decision():
    """保存人类人工核对结果"""
    data = request.json
    document_id = data.get('document_id')
    decision_data = data.get('decision', {})
    
    # 保存人工核对结果
    decision_path = os.path.join(RESULTS_FOLDER, f"{document_id}_decision.json")
    with open(decision_path, 'w', encoding='utf-8') as f:
        json.dump(decision_data, f, ensure_ascii=False, indent=2)
    
    return jsonify({'message': '人工核对结果已保存'})

@app.route('/api/tasks/<task_id>/comparison', methods=['GET'])
def get_task_comparison(task_id):
    """获取指定任务的比对数据，包括schema和多渠道解析结果"""
    try:
        # 读取schema
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema', 'invoice_A2P.json')
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # 读取多渠道解析结果
        results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', f'{task_id}_multi_channel.json')
        with open(results_path, 'r', encoding='utf-8') as f:
            multi_channel_results = json.load(f)
        
        # 组合返回数据
        response_data = {
            "task_id": task_id,
            "schema": schema,
            "comparison_data": multi_channel_results
        }
        
        return jsonify(response_data)
        
    except FileNotFoundError:
        return jsonify({"error": "找不到指定的任务数据"}), 404
    except Exception as e:
        return jsonify({"error": f"获取任务数据失败: {str(e)}"}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取所有可用的任务列表"""
    try:
        results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
        tasks = []
        
        for filename in os.listdir(results_dir):
            if filename.endswith('_multi_channel.json'):
                task_id = filename.replace('_multi_channel.json', '')
                tasks.append({
                    "task_id": task_id,
                    "created_at": os.path.getctime(os.path.join(results_dir, filename))
                })
        
        # 按创建时间排序
        tasks.sort(key=lambda x: x['created_at'], reverse=True)
        return jsonify(tasks)
        
    except Exception as e:
        return jsonify({"error": f"获取任务列表失败: {str(e)}"}), 500

if __name__ == '__main__':
    # port = int(os.environ.get('BACKEND_PORT', 30267))
    app.run(debug=True, host='0.0.0.0', port=5050)
    # get_documents()
