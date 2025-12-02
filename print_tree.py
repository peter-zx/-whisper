import os
import argparse

def tree(dir_path, exclude_dirs):
    # 递归函数，用于遍历目录
    def generate_tree(dir_path, prefix=''):
        dir_path = os.path.normpath(dir_path)
        items = os.listdir(dir_path)
        
        # 排除指定的目录
        dirs = [item for item in items if os.path.isdir(os.path.join(dir_path, item)) and item not in exclude_dirs]
        files = [item for item in items if os.path.isfile(os.path.join(dir_path, item))]
        
        # 合并并排序，让目录显示在文件前面
        items = dirs + files

        for index, item in enumerate(items):
            is_last = index == len(items) - 1
            # 打印当前项
            print(f"{prefix}{'└── ' if is_last else '├── '}{item}")

            # 如果是目录，则继续递归
            if os.path.isdir(os.path.join(dir_path, item)):
                new_prefix = prefix + ('    ' if is_last else '│   ')
                generate_tree(os.path.join(dir_path, item), new_prefix)

    print(os.path.basename(dir_path))
    generate_tree(dir_path)

if __name__ == "__main__":
    # 您可以根据需要修改这里的默认排除列表
    EXCLUDE_DEFAULT = ['__pycache__', '.git', 'venv', 'node_modules', 'whisper_venv']
    
    parser = argparse.ArgumentParser(description="Generate a directory tree with exclusions.")
    parser.add_argument("path", nargs='?', default='.', help="The directory path to start from.")
    
    args = parser.parse_args()
    
    tree(args.path, EXCLUDE_DEFAULT)