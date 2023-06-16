import argparse
import os
import shutil


FOLDER_BLACKLIST = ['__pycache__', '.git', '.vscode', 'env']
FILE_BLACKLIST = ['.gitignore']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Create project copy',
        description=(('Create copy of project in another directory, '
                      'excluding some folders and files. '
                      'Useful for testing.'))
    )
    parser.add_argument('src', help='Source directory')
    parser.add_argument('dst', help='Destination directory')
    args = parser.parse_args()

    src = os.path.abspath(args.src)
    dst = os.path.abspath(args.dst)

    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.mkdir(dst)

    for root, subdirs, files in os.walk(src):
        if os.path.exists(root.replace(src, dst)):
            subdirs = [d for d in subdirs if d not in FOLDER_BLACKLIST]
            files = [f for f in files if f not in FILE_BLACKLIST]
            for subdir in subdirs:
                src_path = os.path.join(root, subdir)
                dst_path = src_path.replace(src, dst)
                os.mkdir(dst_path)
            for file in files:
                src_path = os.path.join(root, file)
                dst_path = src_path.replace(src, dst)
                shutil.copy(src_path, dst_path)

