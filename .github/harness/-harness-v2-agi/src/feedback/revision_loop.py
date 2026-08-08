"""自修正循环 - Harness 的元认知能力"""

import json
from typing import Dict, List, Optional

from src.api.models import ReplicationRequest
from src.config import get_settings
from src.llm.client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AutoRevisionLoop:
    """
    Harness 的自修正能力

    当视觉回归不通过时，自动分析差异并生成修正指令
    """

    def __init__(self):
        self.settings = get_settings()

    async def revise(
        self,
        task_id: str,
        code_package: Dict[str, str],
        visual_feedback: List[Dict],
        aesthetic_feedback: Dict,
        config: ReplicationRequest,
    ) -> Dict[str, str]:
        """执行自修正"""
        logger.info(f"[RevisionLoop] 开始自修正: {task_id}")

        revision_prompt = self._build_revision_prompt(
            visual_feedback, aesthetic_feedback, config
        )

        modified_files = self._identify_files_to_modify(code_package, visual_feedback)

        llm = await get_llm_client()

        for filename in modified_files:
            original_code = code_package[filename]

            prompt = f"""
            以下代码存在视觉还原问题，请修正：

            【文件】: {filename}

            【原始代码】:
            ```tsx
            {original_code}
            ```

            【视觉反馈】:
            {json.dumps(visual_feedback, ensure_ascii=False, indent=2)}

            【审美反馈】:
            {json.dumps(aesthetic_feedback, ensure_ascii=False, indent=2)}

            【修正规则】:
            1. 仅修改与反馈相关的部分，保持其他代码不变
            2. 必须使用设计令牌，禁止引入新的硬编码值
            3. 保持组件接口不变
            4. 输出完整的修正后代码

            请输出修正后的完整代码。
            """

            try:
                revised = await llm.chat_completion(
                    messages=[
                        {"role": "system", "content": "你是前端代码修正专家。"},
                        {"role": "user", "content": prompt},
                    ],
                    stage="refinement",
                    temperature=0.1,
                )

                code_package[filename] = self._extract_code(revised)

            except Exception as e:
                logger.error(f"修正失败 {filename}: {e}")

        return code_package

    def _build_revision_prompt(
        self, visual: List[Dict], aesthetic: Dict, config: ReplicationRequest
    ) -> str:
        """构建修正策略"""
        strategies = []

        for v in visual:
            if v["severity"] == "high":
                strategies.append(f"修复区域 {v['region']}: {v['suggestion']}")

        if not aesthetic.get("passed"):
            for v in aesthetic.get("violations", []):
                strategies.append(f"审美修正: {v['message']}")

        return "\n".join(strategies)

    def _identify_files_to_modify(
        self, code_package: Dict[str, str], feedback: List[Dict]
    ) -> List[str]:
        """识别需要修改的文件"""
        return [
            k for k in code_package.keys()
            if k.startswith("components/") and k.endswith(".tsx")
        ]

    def _extract_code(self, response: str) -> str:
        """从 LLM 响应提取代码"""
        import re
        match = re.search(r'```(?:tsx|jsx|typescript)?\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()


class HumanFeedbackLoop:
    """人工介入修正循环"""

    async def inject_feedback(self, task_id: str, feedback: str):
        """注入人工反馈"""
        logger.info(f"[HumanFeedback] 任务 {task_id} 收到人工反馈")
        pass
