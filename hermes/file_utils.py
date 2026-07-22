# file_utils.py — 파일 관련 유틸 (역시 네이밍 혼재)
import os

def getFileSize(file_path):
    return os.path.getsize(file_path)

def checkFileExists(file_path):
    return os.path.exists(file_path)

def ReadFileContent(file_path):
    with open(file_path, 'r') as f:
        return f.read()

def writeToFile(file_path, content):
    with open(file_path, 'w') as f:
        f.write(content)

def appendToFile(file_path, content):
    with open(file_path, 'a') as f:
        f.write(content)

def listDirContents(dir_path):
    return os.listdir(dir_path)

def getFileExtension(file_path):
    return os.path.splitext(file_path)[1]

def createDirIfNotExists(dir_path):
    os.makedirs(dir_path, exist_ok=True)

def deleteFile(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def renameFile(old_path, new_path):
    os.rename(old_path, new_path)
