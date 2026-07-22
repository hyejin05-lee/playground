# data_processor.py — 데이터 처리 관련 함수 (역시 네이밍 혼재)
def readCsvFile(file_path):
    import csv
    with open(file_path) as f:
        return list(csv.reader(f))

def filterEmptyRows(rows):
    return [r for r in rows if any(cell.strip() for cell in r)]

def SortByColumn(rows, col_index=0):
    return sorted(rows, key=lambda r: r[col_index] if col_index < len(r) else "")

def removeDuplicates(lst):
    seen = set()
    result = []
    for item in lst:
        key = tuple(item) if isinstance(item, list) else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

def flattenList(nested):
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flattenList(item))
        else:
            result.append(item)
    return result

def chunkList(lst, chunkSize=3):
    return [lst[i:i+chunkSize] for i in range(0, len(lst), chunkSize)]

def mergeDicts(dict1, dict2):
    merged = dict1.copy()
    merged.update(dict2)
    return merged

def filterByThreshold(values, minVal=0, maxVal=100):
    return [v for v in values if minVal <= v <= maxVal]

def calculateAverage(numbers):
    return sum(numbers) / len(numbers) if numbers else 0

def findMaxValue(numbers):
    return max(numbers) if numbers else None

def findMinValue(numbers):
    return min(numbers) if numbers else None

def countOccurrences(lst, target):
    return lst.count(target)
