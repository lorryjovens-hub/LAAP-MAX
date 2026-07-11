"""
CUA-Driver 完整窗口操作测试脚本（最终版）

使用 subprocess 启动记事本，然后用 cua-driver 进行操作
"""
import sys
sys.path.insert(0, 'D:/LAAP')
import subprocess
import time

from laap.agent_core.tools.cua_driver_tools import (
    get_screen_size, list_windows, check_permissions,
    get_cursor_position, start_session, end_session,
    mouse_click, type_text, close_window, bring_to_front
)


def find_notepad_window():
    """查找记事本窗口"""
    result = list_windows()
    structured = result.get('structuredContent', {})
    windows = structured.get('windows', [])
    notepad_windows = [w for w in windows 
                       if 'notepad' in w.get('title', '').lower()]
    return notepad_windows[0] if notepad_windows else None


def test_mouse_click_and_type():
    print('=== CUA-Driver 鼠标点击和键盘输入测试 ===')
    print()

    session_id = 'test-laap-final2'
    pid = None
    window_id = None

    # Step 1: 开始会话
    print('1. start_session(%s)' % session_id)
    result = start_session(session_id)
    is_error = result.get('isError')
    print('   isError:', is_error)
    if is_error:
        print('   ✗ 失败:', result)
        return False
    print('   ✓ 成功')

    # Step 2: 使用 subprocess 启动记事本
    print()
    print('2. 启动记事本 (subprocess)...')
    try:
        proc = subprocess.Popen(['notepad.exe'])
        time.sleep(2)
        print('   ✓ 启动成功')
    except Exception as e:
        print('   ✗ 启动失败:', e)
        end_session(session_id)
        return False

    # Step 3: 查找记事本窗口
    print()
    print('3. 查找记事本窗口...')
    for _ in range(5):
        window_info = find_notepad_window()
        if window_info:
            pid = window_info.get('pid')
            window_id = window_info.get('window_id')
            title = window_info.get('title')
            print('   ✓ 找到窗口: PID=%s, WindowID=%s, Title=%s' % (pid, window_id, title))
            break
        time.sleep(1)
    else:
        print('   ✗ 未找到记事本窗口')
        end_session(session_id)
        return False

    # Step 4: 前置窗口
    print()
    print('4. bring_to_front(window_id=%s)' % window_id)
    result = bring_to_front(window_id)
    is_error = result.get('isError')
    print('   isError:', is_error)
    if is_error:
        print('   警告:', result)
    time.sleep(0.5)

    # Step 5: 获取光标位置（测试前）
    print()
    print('5. get_cursor_position (测试前)')
    result = get_cursor_position()
    pos = result.get('structuredContent', {})
    print('   光标位置: (%d, %d)' % (pos.get('x', 0), pos.get('y', 0)))

    # Step 6: 鼠标点击
    print()
    print('6. mouse_click(x=100, y=100, pid=%s)' % pid)
    result = mouse_click(100, 100, pid=pid, window_id=window_id)
    is_error = result.get('isError')
    print('   isError:', is_error)
    if is_error:
        print('   ✗ 点击失败:', result)
    else:
        print('   ✓ 点击成功')
    time.sleep(0.5)

    # Step 7: 键盘输入
    print()
    print('7. type_text(text=\"Hello from LAAP CUA-Driver!\", pid=%s)' % pid)
    result = type_text('Hello from LAAP CUA-Driver!', pid=pid, window_id=window_id)
    is_error = result.get('isError')
    print('   isError:', is_error)
    if is_error:
        print('   ✗ 输入失败:', result)
    else:
        print('   ✓ 输入成功')
    time.sleep(0.5)

    # Step 8: 获取光标位置（测试后）
    print()
    print('8. get_cursor_position (测试后)')
    result = get_cursor_position()
    pos = result.get('structuredContent', {})
    print('   光标位置: (%d, %d)' % (pos.get('x', 0), pos.get('y', 0)))

    # Step 9: 等待用户查看效果
    print()
    print('9. 等待 5 秒让用户查看效果...')
    time.sleep(5)

    # Step 10: 关闭窗口
    print()
    print('10. close_window(window_id=%s)' % window_id)
    if window_id:
        result = close_window(window_id)
        is_error = result.get('isError')
        print('   isError:', is_error)
        if is_error:
            print('   ✗ 关闭失败:', result)
        else:
            print('   ✓ 关闭成功')

    # Step 11: 结束会话
    print()
    print('11. end_session(%s)' % session_id)
    result = end_session(session_id)
    is_error = result.get('isError')
    print('   isError:', is_error)
    if is_error:
        print('   ✗ 结束失败:', result)
    else:
        print('   ✓ 结束成功')

    print()
    print('=== 测试完成 ===')
    return True


if __name__ == '__main__':
    print('正在测试 CUA-Driver mouse_click 和 type_text...')
    print()
    
    if test_mouse_click_and_type():
        print('✓ 所有测试通过!')
    else:
        print('✗ 测试失败')
