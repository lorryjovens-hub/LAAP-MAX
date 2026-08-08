import requests
import os
from bs4 import BeautifulSoup

sites = [
    "https://zhiyingsheng-lorry.netlify.app/",
    "https://zhiyingsheng3d.netlify.app/",
    "https://clawlink.netlify.app/",
    "https://clawlink-edge-lorry.netlify.app/",
    "https://clawlink-dashboard.netlify.app/",
    "https://clawlink-trilayer.netlify.app/",
    "https://bioneural-ai.netlify.app/",
    "https://aishop-lorry.netlify.app",
    "https://esp32-lorry.netlify.app/",
    "https://memoradb.netlify.app/",
    "https://ai-applicantion.netlify.app/",
    "https://quantitative-trading.netlify.app/",
    "https://scintillating-tarsier-b73c49.netlify.app/",
    "https://gitbox.netlify.app/",
    "https://jarvispm.netlify.app/"
]

results = []

for site in sites:
    try:
        print(f"Analyzing {site}...")
        resp = requests.get(site, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        title = soup.title.string if soup.title else "No title"
        tech_stack = []
        
        # 检测技术栈
        if any(['react' in script.get('src', '').lower() for script in soup.find_all('script')]):
            tech_stack.append("React")
        if any(['vue' in script.get('src', '').lower() for script in soup.find_all('script')]):
            tech_stack.append("Vue")
        if any(['vite' in script.get('src', '').lower() for script in soup.find_all('script')]):
            tech_stack.append("Vite")
        if any(['three' in script.get('src', '').lower() for script in soup.find_all('script')]):
            tech_stack.append("ThreeJS/3D")
        if any(['tailwind' in link.get('href', '').lower() for link in soup.find_all('link', rel='stylesheet')]):
            tech_stack.append("Tailwind CSS")
        
        has_root = soup.find('div', id='root') is not None
        if has_root:
            tech_stack.append("SPA")
        
        results.append({
            "url": site,
            "title": title.strip(),
            "tech_stack": tech_stack,
            "status": resp.status_code
        })
    except Exception as e:
        results.append({
            "url": site,
            "title": "Error",
            "tech_stack": [],
            "status": str(e)
        })

# 保存结果
output_path = os.path.join(os.path.dirname(__file__), '../references/lorry_sites_analysis.md')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("# Lorry 个人站点分析报告\n\n")
    f.write("| 站点URL | 标题 | 技术栈 | 状态 |\n")
    f.write("| --- | --- | --- | --- |\n")
    for res in results:
        tech = ', '.join(res['tech_stack']) if res['tech_stack'] else '未识别'
        f.write(f"| {res['url']} | {res['title']} | {tech} | {res['status']} |\n")
    
    f.write("\n## 风格特点总结\n")
    f.write("- 全部采用Netlify部署，属于静态站点/SPA应用\n")
    f.write("- 主流技术栈：React + Vite + Tailwind CSS 为主\n")
    f.write("- 包含3D应用、管理后台、AI应用、量化交易、IoT等多种类型项目\n")

print("Analysis completed! Results saved to lorry_sites_analysis.md")
