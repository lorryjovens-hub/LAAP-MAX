def bubble_sort(arr):
    """冒泡排序算法（升序）"""
    n = len(arr)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        # 如果本轮未发生交换，说明已经有序，提前结束
        if not swapped:
            break
    return arr


if __name__ == "__main__":
    # 测试用例
    test_cases = [
        [64, 34, 25, 12, 22, 11, 90],
        [5, 1, 4, 2, 8],
        [1, 2, 3, 4, 5],
        [5, 4, 3, 2, 1],
        [1],
        [],
        [3, 3, 2, 1, 2],
    ]

    for case in test_cases:
        original = case[:]
        sorted_arr = bubble_sort(case)
        print(f"原始: {original} -> 排序后: {sorted_arr}")
