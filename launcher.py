#!/usr/bin/env python3
"""
Union AI API - 图形化启动器
提供简单的 GUI 界面来管理 Docker 服务
"""

import subprocess
import sys
import os
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading


class UnionAILauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Union AI API 启动器")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 获取脚本所在目录
        self.script_dir = Path(__file__).parent.absolute()
        self.compose_file = self.script_dir / "docker-compose.clean.yml"
        
        # 设置样式
        self.setup_styles()
        
        # 创建 UI
        self.create_widgets()
        
        # 检查 Docker
        self.check_docker()
    
    def setup_styles(self):
        """设置 UI 样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Status.TLabel', font=('Helvetica', 11))
        style.configure('Action.TButton', font=('Helvetica', 11), padding=10)
    
    def create_widgets(self):
        """创建 UI 组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="🚀 Union AI API 启动器",
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 状态框架
        status_frame = ttk.LabelFrame(main_frame, text="服务状态", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Docker 状态
        self.docker_label = ttk.Label(
            status_frame, 
            text="检查中...",
            style='Status.TLabel'
        )
        self.docker_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 容器状态
        self.container_label = ttk.Label(
            status_frame, 
            text="容器状态：检测中...",
            style='Status.TLabel'
        )
        self.container_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # API 服务状态
        self.api_label = ttk.Label(
            status_frame, 
            text="API 服务：检测中...",
            style='Status.TLabel'
        )
        self.api_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # 管理后台状态
        self.web_label = ttk.Label(
            status_frame, 
            text="管理后台：检测中...",
            style='Status.TLabel'
        )
        self.web_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(0, 20))
        
        # 启动按钮
        self.start_button = ttk.Button(
            button_frame,
            text="▶️ 启动服务",
            command=self.start_service,
            style='Action.TButton'
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        # 停止按钮
        self.stop_button = ttk.Button(
            button_frame,
            text="⏹️ 停止服务",
            command=self.stop_service,
            style='Action.TButton'
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # 重启按钮
        self.restart_button = ttk.Button(
            button_frame,
            text="🔄 重启服务",
            command=self.restart_service,
            style='Action.TButton'
        )
        self.restart_button.grid(row=0, column=2, padx=5)
        
        # 打开浏览器按钮
        self.browser_button = ttk.Button(
            button_frame,
            text="🌐 打开管理后台",
            command=self.open_browser,
            style='Action.TButton'
        )
        self.browser_button.grid(row=0, column=3, padx=5)
        
        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=('Courier', 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置框架
        config_frame = ttk.Frame(main_frame)
        config_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        # 数据目录
        data_dir = self.script_dir / "data"
        ttk.Label(
            config_frame,
            text=f"📂 数据目录：{data_dir}",
            foreground='gray'
        ).grid(row=0, column=0, sticky=tk.W)
        
        # 访问地址
        ttk.Label(
            config_frame,
            text="🌐 API: http://localhost:18080 | 管理后台：http://localhost:18501",
            foreground='blue'
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # 配置网格权重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
    
    def log(self, message):
        """添加日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def check_docker(self):
        """检查 Docker 状态"""
        def check():
            try:
                # 检查 Docker 是否安装
                result = subprocess.run(
                    ['docker', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.docker_label.config(text=f"✓ {result.stdout.strip()}", foreground='green')
                    self.log(f"Docker 已安装：{result.stdout.strip()}")
                else:
                    self.docker_label.config(text="✗ Docker 未安装", foreground='red')
                    self.log("Docker 未安装")
                    return
                
                # 检查 Docker 是否运行
                result = subprocess.run(
                    ['docker', 'ps'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    self.docker_label.config(text="✗ Docker 未运行", foreground='red')
                    self.log("Docker 未运行，请启动 Docker Desktop")
                    return
                
                # 检查容器状态
                result = subprocess.run(
                    ['docker', 'ps', '-a', '--filter', 'name=union-ai-api', '--format', '{{.Status}}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if 'Up' in result.stdout:
                    self.container_label.config(text="✓ 容器状态：运行中", foreground='green')
                    self.api_label.config(text="✓ API 服务：http://localhost:18080", foreground='green')
                    self.web_label.config(text="✓ 管理后台：http://localhost:18501", foreground='green')
                    self.log("服务已运行")
                    self.start_button.config(state='disabled')
                elif 'Exited' in result.stdout:
                    self.container_label.config(text="⚠ 容器状态：已停止", foreground='orange')
                    self.api_label.config(text="✗ API 服务：未运行", foreground='red')
                    self.web_label.config(text="✗ 管理后台：未运行", foreground='red')
                    self.log("容器已停止")
                    self.start_button.config(state='normal')
                else:
                    self.container_label.config(text="容器状态：未创建", foreground='gray')
                    self.api_label.config(text="API 服务：未启动", foreground='gray')
                    self.web_label.config(text="管理后台：未启动", foreground='gray')
                    self.log("容器未创建")
                    self.start_button.config(state='normal')
                    
            except subprocess.TimeoutExpired:
                self.docker_label.config(text="✗ 检查超时", foreground='red')
                self.log("Docker 检查超时")
            except FileNotFoundError:
                self.docker_label.config(text="✗ Docker 未安装", foreground='red')
                self.log("Docker 未安装，请先安装 Docker Desktop")
            except Exception as e:
                self.docker_label.config(text=f"✗ 错误：{str(e)}", foreground='red')
                self.log(f"检查失败：{str(e)}")
        
        threading.Thread(target=check, daemon=True).start()
    
    def run_command(self, command, description):
        """运行命令"""
        def run():
            try:
                self.log(f"正在{description}...")
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.script_dir,
                    timeout=300
                )
                
                if result.returncode == 0:
                    self.log(f"✓ {description}成功")
                    if result.stdout:
                        self.log(result.stdout)
                else:
                    self.log(f"✗ {description}失败")
                    if result.stderr:
                        self.log(result.stderr)
                    messagebox.showerror("错误", f"{description}失败:\n{result.stderr}")
                
                # 刷新状态
                self.check_docker()
                
            except subprocess.TimeoutExpired:
                self.log(f"✗ {description}超时")
                messagebox.showerror("错误", f"{description}超时")
            except Exception as e:
                self.log(f"✗ 错误：{str(e)}")
                messagebox.showerror("错误", f"发生错误:\n{str(e)}")
        
        threading.Thread(target=run, daemon=True).start()
    
    def start_service(self):
        """启动服务"""
        if not self.compose_file.exists():
            messagebox.showerror("错误", f"找不到配置文件:\n{self.compose_file}")
            return
        
        self.run_command(
            f"./start.sh",
            "启动服务"
        )
    
    def stop_service(self):
        """停止服务"""
        if messagebox.askyesno("确认", "确定要停止服务吗？"):
            self.run_command(
                f"./stop.sh",
                "停止服务"
            )
    
    def restart_service(self):
        """重启服务"""
        if messagebox.askyesno("确认", "确定要重启服务吗？"):
            self.run_command(
                f"./restart.sh",
                "重启服务"
            )
    
    def open_browser(self):
        """打开浏览器"""
        webbrowser.open('http://localhost:18501')
        self.log("已打开管理后台")


def main():
    root = tk.Tk()
    app = UnionAILauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
