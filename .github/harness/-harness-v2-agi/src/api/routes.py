"""API 路由 - 任务管理与结果查询"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.models import TaskProgress, ReplicationResult
from src.utils.logger import get_logger

router = APIRouter(tags=["replication"])
logger = get_logger(__name__)


@router.get("/tasks/{task_id}/status", response_model=TaskProgress)
async def get_task_status(task_id: str):
    """查询任务实时进度"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator
    orchestrator = ReplicationOrchestrator()
    
    progress = await orchestrator.get_progress(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    return progress


@router.get("/tasks/{task_id}/result", response_model=ReplicationResult)
async def get_task_result(task_id: str):
    """获取复现结果"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator
    orchestrator = ReplicationOrchestrator()
    
    result = await orchestrator.get_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 结果不存在")
    
    if result.status == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"复现失败: {result.error_message}"
        )
    
    return result


@router.get("/tasks/{task_id}/download")
async def download_result(task_id: str):
    """下载代码包"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator
    orchestrator = ReplicationOrchestrator()
    
    result = await orchestrator.get_result(task_id)
    if not result or not result.code_package:
        raise HTTPException(status_code=404, detail="代码包未生成")
    
    return FileResponse(
        path=result.code_package,
        filename=f"web-replica-{task_id}.zip",
        media_type="application/zip",
    )


@router.get("/tasks/{task_id}/preview")
async def preview_result(task_id: str):
    """获取预览 URL"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator
    orchestrator = ReplicationOrchestrator()
    
    result = await orchestrator.get_result(task_id)
    if not result or not result.preview_url:
        raise HTTPException(status_code=404, detail="预览不可用")
    
    return {"preview_url": result.preview_url}


@router.post("/tasks/{task_id}/revise")
async def request_revision(
    task_id: str,
    feedback: str = Query(..., description="人工反馈指令"),
):
    """人工介入修正 - HITL (Human-in-the-Loop)"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator
    from src.feedback.revision_loop import HumanFeedbackLoop
    
    orchestrator = ReplicationOrchestrator()
    feedback_loop = HumanFeedbackLoop()
    
    # 注入人工反馈并触发修正
    await feedback_loop.inject_feedback(task_id, feedback)
    await orchestrator.trigger_revision(task_id, feedback)
    
    logger.info(f"[Task {task_id}] 人工修正已注入", extra={"feedback": feedback})
    
    return {"message": "修正指令已接收，Harness 正在重新推理...", "task_id": task_id}
