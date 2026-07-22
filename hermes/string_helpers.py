# string_helpers.py — 함수를 많이 넣어서 반복 리네이밍 작업을 충분히 수행할 수 있도록 구성
def reverseString(s):
    return s[::-1]

def CountWords(s):
    return len(s.split())

def trimSpaces(s):
    return s.strip()

def toUpperCase(s):
    return s.upper()

def toLowerCase(s):
    return s.lower()

def capitalizeFirst(s):
    return s.capitalize()

def replaceSubstring(s, old, new):
    return s.replace(old, new)

def checkStartsWith(s, prefix):
    return s.startswith(prefix)

def checkEndsWith(s, suffix):
    return s.endswith(suffix)

def splitByDelimiter(s, delim=","):
    return s.split(delim)

def joinWithDelimiter(lst, delim="-"):
    return delim.join(lst)

def padLeftZeros(s, width=10):
    return s.zfill(width)

def removePrefix(s, prefix):
    return s[len(prefix):] if s.startswith(prefix) else s

def truncateString(s, max_len=50):
    return s[:max_len] + "..." if len(s) > max_len else s
