#!/usr/bin/env python3
import os
import subprocess
import shutil
import time
import platform
from pathlib import Path

def kill_process(process_name):
    """
    检查并终止指定的进程
    
    Args:
        process_name (str): 要终止的进程名称
        
    Returns:
        bool: 如果成功终止进程或进程不存在则返回True，否则返回False
    """
    system = platform.system()
    
    try:
        print("尝试终止可能正在运行的 ClipTranslate 进程...")
        if system == "Windows":
            # 在Windows上使用tasklist和taskkill
            # 首先检查进程是否存在
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}"], 
                capture_output=True, 
                text=True
            )
            
            # 如果进程存在（输出中包含进程名）
            if process_name in result.stdout:
                print(f"发现正在运行的 {process_name} 进程，尝试终止...")
                
                # 尝试终止进程
                kill_result = subprocess.run(
                    ["taskkill", "/F", "/IM", process_name],
                    capture_output=True,
                    text=True
                )
                
                if kill_result.returncode == 0:
                    print(f"成功终止 {process_name} 进程")
                    # 给系统一些时间来完全释放文件
                    time.sleep(1)
                    return True
                else:
                    print(f"无法终止 {process_name} 进程: {kill_result.stderr}")
                    return False
            else:
                print(f"未发现正在运行的 {process_name} 进程")
                return True
        
        elif system == "Linux" or system == "Darwin":  # Linux or macOS
            # 在Linux/macOS上使用pkill
            result = subprocess.run(
                ["pkill", "-f", process_name],
                capture_output=True,
                text=True
            )
            
            # pkill返回0表示成功找到并终止了进程，返回1表示没有找到进程
            if result.returncode == 0:
                print(f"成功终止 {process_name} 进程")
                time.sleep(1)
            else:
                print(f"未发现正在运行的 {process_name} 进程")
            
            return True
        
        else:
            print(f"不支持的操作系统: {system}")
            return False
            
    except Exception as e:
        print(f"尝试终止进程时出错: {e}")
        return False

def main():
    print("开始构建应用程序...")
    
    # 终止可能正在运行的ClipTranslate进程
    if not kill_process("ClipTranslate.exe"):
        user_input = input("无法终止现有进程。是否继续构建? (y/n): ")
        if user_input.lower() != 'y':
            print("构建已取消。")
            return
    
    # 执行 PyInstaller 命令
    try:
        print("正在执行 PyInstaller...")
        # 使用 subprocess.run 执行命令并等待其完成
        result = subprocess.run(
            ["pyinstaller", "clipTranslate.spec", "-y"], 
            check=True,  # 如果命令返回非零状态，将引发异常
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # 将输出作为文本而不是字节
        )
        
        # 打印命令输出
        print("PyInstaller 命令输出:")
        print(result.stdout)
        
        if result.stderr:
            print("PyInstaller 错误/警告:")
            print(result.stderr)
            
        print("PyInstaller 构建完成.")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller 构建失败，错误码: {e.returncode}")
        print(f"错误输出: {e.stderr}")
        return
    except FileNotFoundError:
        print("错误: 未找到 pyinstaller 命令。请确保已安装 PyInstaller。")
        return
    
    # 复制 icons 文件夹
    src_icons = Path("icons")
    dst_icons = Path("dist/ClipTranslate/icons")
    
    if not src_icons.exists():
        print(f"警告: 源图标文件夹 '{src_icons}' 不存在.")
        return
    
    # 确保目标目录存在
    dst_parent = Path("dist/ClipTranslate")
    if not dst_parent.exists():
        print(f"警告: 目标目录 '{dst_parent}' 不存在. PyInstaller 可能未成功创建输出目录。")
        return
    
    print(f"正在复制图标文件夹 '{src_icons}' 到 '{dst_icons}'...")
    
    try:
        # 如果目标目录已存在，先删除它
        if dst_icons.exists():
            shutil.rmtree(dst_icons)
        
        # 复制整个文件夹
        shutil.copytree(src_icons, dst_icons)
        print("文件夹复制完成.")
    except Exception as e:
        print(f"复制图标文件夹时出错: {e}")
        return
    
    print("构建过程完成!")
    print(f"应用程序已构建到: {os.path.abspath(dst_parent)}")

if __name__ == "__main__":
    main()
