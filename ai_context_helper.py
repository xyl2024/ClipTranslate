"""
    该脚本读取并输出当前项目的所有 .py 文件, 用于提供给AI作为上下文.
    仅适用于小型项目.
    用法: 运行脚本获取项目文件内容, 将代码发送给 gpt, 随后进行代码的提问.
"""
import os

def read_py_files_and_save(output_file, exclude_files, exclude_dirs):
    current_dir = os.getcwd()
    file_cnt = 0
    if exclude_files is None:
        exclude_files = []
    if exclude_dirs is None:
        exclude_dirs = []

    with open(output_file, 'w', encoding='utf-8') as f:
        for root, dirs, files in os.walk(current_dir): # 递归遍历当前目录及其子目录
            # 过滤掉隐藏文件夹以及指定目录，例如 .venv
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                if file.endswith('.py') and file not in exclude_files and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, start=current_dir)
                    
                    f.write(f'{relative_path}：\n') # 将相对路径格式化输出
                    print(f"{relative_path}")
                    file_cnt = file_cnt + 1
                    try:
                        with open(file_path, 'r', encoding='utf-8') as py_file:
                            content = py_file.read()
                            f.write(f'```python\n{content}\n```\n\n') # 输出文件内容
                    except Exception as e:
                        f.write(f'无法读取文件: {relative_path}, 错误: {e}\n\n')
    return file_cnt

if __name__ == '__main__':
    output_file = 'output.txt'
    
    # 指定需要过滤的文件列表和目录列表
    exclude_files = ["ai_context_helper.py", "check_env.py", "build.py"]
    exclude_dirs = ["test", "log", "resources", "config", "experiments"]

    file_cnt = read_py_files_and_save(output_file, exclude_files, exclude_dirs)
    print(f'共 {file_cnt} 个Python文件的内容已经输出到 {output_file}')
