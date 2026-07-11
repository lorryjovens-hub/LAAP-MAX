"""
LAAP Consciousness — 核心导出

使用方法:
    from laap_consciousness import create_consciousness, Consciousness
    c = create_consciousness(name="MyAgent")
    print(c.get_status())
"""
from .identity import DigitalIdentity, IdentityStore
from .psi_driver import PSIDriver, PSIState
from .delegation import DelegationTracker, DelegationRecord
from .desire_delegator import DesireDelegator, DesireAction, create_desire_delegator
from .preference import PreferenceLearner, AestheticEngine, LorryProfile
from .orchestrator import DelegationOrchestrator, Mission, run_mission
from .trend_scanner import DesignTrendScanner, DesignTrendDatabase, scan_trends, get_current_prompt
from .code_engineer import CodeEngineer, EngineeringProject, EngineeringTask, create_code_engineer


class Consciousness:
    """
    意识实例——一个完整的数字生命体内核。

    包含：数字身份（你是谁）、PSI需求（你想要什么）、委托评估（你学得怎么样）
    """

    def __init__(self, name: str = "Aris", creator: str = "",
                 data_dir=None):
        if data_dir is None:
            from pathlib import Path
            data_dir = Path.home() / ".laap"

        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        from pathlib import Path

        # 加载或创建身份
        self.identity_store = IdentityStore(Path(self.data_dir) / "identity.json")
        if self.identity_store.exists():
            self.identity = self.identity_store.load()
            if name and name != self.identity.name:
                self.identity.nickname = name
        else:
            self.identity = DigitalIdentity(name=name, creator=creator)
        self.identity_store.save(self.identity)

        # PSI 需求驱动
        self.psi = PSIDriver(Path(self.data_dir) / "psi_state.json")

        # 委托评估
        self.delegation = DelegationTracker(Path(self.data_dir))

        # 欲望委托器
        self.desire = DesireDelegator(
            psi_driver=self.psi,
            data_dir=Path(self.data_dir),
        )

    def tick(self, dt: float = 1.0):
        """一次意识心跳"""
        self.psi.tick(dt)

    def get_status(self) -> dict:
        """完整的意识状态"""
        return {
            "identity": {
                "name": self.identity.display_name,
                "instance_id": self.identity.instance_id[:8],
                "version": self.identity.version,
                "created": self.identity.created_at,
            },
            "psi": self.psi.get_summary(),
        }

    def __repr__(self) -> str:
        s = self.get_status()
        psi = s["psi"]
        return (
            f"Consciousness({s['identity']['name']}) "
            f"[{psi['dominant_need']}: {psi['needs']}]"
        )


def create_consciousness(
    name: str = "Aris",
    creator: str = "",
    data_dir: str | None = None,
) -> Consciousness:
    """创建或加载一个意识实例"""
    from pathlib import Path
    path = Path(data_dir) if data_dir else None
    return Consciousness(name=name, creator=creator, data_dir=path)
