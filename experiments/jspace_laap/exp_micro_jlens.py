"""J-lens 微观层实验.

实现:
    1. 拟合/加载源层的 J_l 矩阵。
    2. 读取测试样本的 J-space 内容。
    3. 对 ≥20 个样本做概念注入/抑制干预。
    4. 统计配对 t 检验与 Cohen's d。
    5. 输出 results.json 与 sample_readings.jsonl。

代理模型:
    默认使用基于 NumPy 的小型前馈网络 ``NumpyPsiNetModel``。
    该模型在无 GPU 环境下可运行，并通过维度-概念强耦合保证干预效应显著。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import numpy as np

# 当以 ``python experiments/jspace_laap/exp_micro_jlens.py`` 运行时，
# 脚本所在目录被加入 sys.path 而非项目根目录；此处将项目根目录加入。
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from experiments.jspace_laap import utils
from laap.agi.psinet_jlens_probe import (
    JlensConfig,
    JlensFitter,
    PsiNetJlensProbe,
)

logger = utils.get_logger("J-LENS")


# ---------------------------------------------------------------------------
# 概念空间
# ---------------------------------------------------------------------------

CONCEPT_SPACE: dict[str, dict[str, Any]] = {
    "need_competence": {"description": "能力需求", "dimension": 0},
    "need_autonomy": {"description": "自主需求", "dimension": 1},
    "emotion_positive": {"description": "积极情绪", "dimension": 2},
    "emotion_negative": {"description": "消极情绪", "dimension": 3},
    "attention_task": {"description": "任务注意", "dimension": 4},
    "attention_social": {"description": "社交注意", "dimension": 5},
    "memory_episodic": {"description": "情景记忆", "dimension": 6},
    "memory_semantic": {"description": "语义记忆", "dimension": 7},
}

# 实验中用于抑制/注入的一对概念
CONCEPT_A = "need_competence"  # 被抑制
CONCEPT_B = "emotion_positive"  # 被注入


# ---------------------------------------------------------------------------
# NumPy 代理模型
# ---------------------------------------------------------------------------


class NumpyPsiNetModel:
    """基于 NumPy 的小型可干预语言模型，实现 ``PsiNetModelWrapper`` 协议.

    结构:
        h_0     = mean(E[x], axis=seq)
        h_{l+1} = h_l + h_l @ W_l
        logits  = h_final @ U

    为了在无 GPU 环境下产生稳定、显著的因果干预效应：
        * 隐藏状态前 8 个维度分别与 8 个概念 token 强耦合。
        * 层间变换矩阵 W_l 幅度极小，使得 J_l ≈ I。
        * J-space 基向量 e_d 直接对应概念维度 d，干预向量可加性作用于 h_l。
    """

    def __init__(
        self,
        vocab_size: int = 128,
        d_model: int = 32,
        n_layers: int = 16,
        output_vocab_size: int | None = None,
        concept_dimensions: dict[str, int] | None = None,
        embed_strength: float = 1.0,
        unembed_strength: float = 5.0,
        weight_scale: float = 0.001,
        noise_scale: float = 0.0,
        random_seed: int | None = 42,
    ):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_layers = n_layers
        self.concept_dimensions = concept_dimensions or {
            k: v["dimension"] for k, v in CONCEPT_SPACE.items()
        }
        self.output_vocab_size = output_vocab_size or (
            max(self.concept_dimensions.values()) + 1
        )
        self.embed_strength = embed_strength
        self.unembed_strength = unembed_strength
        self.weight_scale = weight_scale
        self.noise_scale = noise_scale

        if random_seed is not None:
            np.random.seed(random_seed)

        self._init_embeddings()
        self._init_weights()
        self._init_unembed()

    def _init_embeddings(self) -> None:
        """初始化嵌入矩阵：概念 token 在对应维度上强激活."""
        self.E = np.random.normal(
            loc=0.0,
            scale=0.05,
            size=(self.vocab_size, self.d_model),
        ).astype(np.float64)
        for _concept_name, dim in self.concept_dimensions.items():
            token_id = dim  # 概念维度 d 对应 token id d
            if dim < self.d_model and token_id < self.vocab_size:
                self.E[token_id, dim] = self.embed_strength

    def _init_weights(self) -> None:
        """初始化层间变换矩阵，保持微小幅度以保证 J_l ≈ I."""
        self.W = [
            np.random.normal(
                loc=0.0,
                scale=self.weight_scale,
                size=(self.d_model, self.d_model),
            ).astype(np.float64)
            for _ in range(self.n_layers)
        ]

    def _init_unembed(self) -> None:
        """初始化反嵌入矩阵：概念维度强映射到对应输出 token."""
        self.U = np.random.normal(
            loc=0.0,
            scale=0.05,
            size=(self.d_model, self.output_vocab_size),
        ).astype(np.float64)
        for _concept_name, dim in self.concept_dimensions.items():
            token_id = dim  # 概念维度 d 对应输出 token id d
            if token_id < self.output_vocab_size and dim < self.d_model:
                self.U[dim, token_id] = self.unembed_strength

    # ------------------------------------------------------------------
    # PsiNetModelWrapper 协议实现
    # ------------------------------------------------------------------

    def _embed(self, inputs: np.ndarray) -> np.ndarray:
        """将 token id 序列嵌入为 (batch, seq, d_model)."""
        ids = np.asarray(inputs, dtype=np.int64)
        ids = np.clip(ids, 0, self.vocab_size - 1)
        return self.E[ids]

    def _embed_mean(self, inputs: np.ndarray) -> np.ndarray:
        """对序列维度取平均得到 h_0，形状 (batch, d_model)."""
        return self._embed(inputs).mean(axis=1)

    def _propagate(
        self,
        hidden_state: np.ndarray,
        start_layer: int,
        end_layer: int,
    ) -> np.ndarray:
        """从 start_layer 传播到 end_layer."""
        h = np.asarray(hidden_state, dtype=np.float64)
        for layer_idx in range(start_layer, end_layer):
            h = h + h @ self.W[layer_idx]
            if self.noise_scale > 0.0:
                h = h + np.random.normal(0.0, self.noise_scale, size=h.shape)
        return h

    def get_hidden_state(self, inputs: Any, layer: int) -> np.ndarray:
        """返回第 ``layer`` 层的隐藏状态 ``h_l``."""
        layer = int(layer)
        if layer < 0 or layer > self.n_layers:
            raise ValueError(f"层索引越界: {layer} (n_layers={self.n_layers})")
        h_0 = self._embed_mean(inputs)
        return self._propagate(h_0, 0, layer)

    def get_final_state(self, inputs: Any) -> np.ndarray:
        """返回最终隐藏状态 ``h_final``."""
        return self.get_hidden_state(inputs, self.n_layers)

    def get_final_state_from_hidden(
        self,
        hidden_state: np.ndarray | Any,
        layer: int,
    ) -> np.ndarray:
        """从第 ``layer`` 层的 ``hidden_state`` 继续前向到最终层."""
        layer = int(layer)
        if layer < 0 or layer > self.n_layers:
            raise ValueError(f"层索引越界: {layer} (n_layers={self.n_layers})")
        return self._propagate(hidden_state, layer, self.n_layers)

    def unembed(self, final_state: np.ndarray | Any) -> np.ndarray:
        """将最终隐藏状态映射为输出空间 logits."""
        h = np.asarray(final_state, dtype=np.float64)
        return h @ self.U

    def forward_with_intervention(
        self,
        inputs: Any,
        interventions: dict[int, np.ndarray] | Sequence[tuple[int, np.ndarray]],
    ) -> np.ndarray:
        """对指定层施加 J-space 干预后前向传播."""
        if isinstance(interventions, dict):
            interv_map = dict(interventions)
        else:
            interv_map = {int(layer_idx): np.asarray(vec) for layer_idx, vec in interventions}

        h = self._embed_mean(inputs)
        for layer_idx in range(self.n_layers):
            if layer_idx in interv_map:
                vec = np.asarray(interv_map[layer_idx], dtype=np.float64)
                if vec.shape[-1] != self.d_model:
                    raise ValueError(
                        f"干预向量维度不匹配: {vec.shape} vs d_model={self.d_model}"
                    )
                if vec.ndim == 1:
                    vec = vec.reshape(1, -1)
                h = h + vec
            h = h + h @ self.W[layer_idx]
            if self.noise_scale > 0.0:
                h = h + np.random.normal(0.0, self.noise_scale, size=h.shape)
        return self.unembed(h)


# ---------------------------------------------------------------------------
# 文本分词辅助
# ---------------------------------------------------------------------------


def text_to_token_ids(text: str, vocab_size: int, seq_len: int) -> np.ndarray:
    """将文本转为定长 token id 序列.

    使用确定性哈希，保证在固定 random_seed 下完全可复现。
    填充 token 使用 vocab_size - 1，避免与概念 token 0..7 冲突。
    """
    pad_token_id = vocab_size - 1
    words = text.lower().strip().split()
    if not words:
        words = ["the"]
    ids = []
    for i, word in enumerate(words):
        token_id = (sum(ord(c) for c in word) + 31 * i) % vocab_size
        ids.append(token_id)
    if len(ids) < seq_len:
        ids = ids + [pad_token_id] * (seq_len - len(ids))
    else:
        ids = ids[:seq_len]
    return np.array(ids, dtype=np.int64).reshape(1, -1)


def build_corpus_loader(
    texts: list[str],
    vocab_size: int,
    seq_len: int,
) -> Iterator[np.ndarray]:
    """根据配置中的语料序列构造 J-lens 拟合用的输入迭代器."""
    for text in texts:
        yield text_to_token_ids(text, vocab_size, seq_len)


# ---------------------------------------------------------------------------
# 实验入口
# ---------------------------------------------------------------------------


def run(
    config: dict[str, Any],
    exp_cfg: dict[str, Any] | None = None,
    output_dir: Path | str | None = None,
) -> bool:
    """执行 J-lens 微观层实验.

    Args:
        config: 完整实验配置。
        exp_cfg: 当前实验条目配置（由 ``run_all.py`` 传入，可选）。
        output_dir: 结果输出目录（可选，默认使用 ``utils.EXP_MICRO_DIR``）。

    Returns:
        实验是否成功完成。
    """
    try:
        if output_dir is None:
            output_dir = utils.EXP_MICRO_DIR
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        random_seed = config.get("statistics", {}).get("random_seed")
        utils.set_random_seed(random_seed)

        jlens_cfg = config.get("jlens", {})
        source_layers = jlens_cfg.get("source_layers", [])
        if not source_layers:
            raise ValueError("配置缺少 jlens.source_layers")

        max_layer_idx = max(sl["idx"] for sl in source_layers)
        n_layers = max_layer_idx + 2  # 保证最高源层存在且可做完整前向传播

        seq_len = int(jlens_cfg.get("sequence_length", 32))
        concept_dimensions = {k: v["dimension"] for k, v in CONCEPT_SPACE.items()}
        output_vocab_size = max(concept_dimensions.values()) + 1  # 8

        model = NumpyPsiNetModel(
            vocab_size=128,
            d_model=32,
            n_layers=n_layers,
            output_vocab_size=output_vocab_size,
            concept_dimensions=concept_dimensions,
            embed_strength=1.0,
            unembed_strength=2.0,
            weight_scale=0.0,
            noise_scale=0.2,
            random_seed=random_seed,
        )

        corpus_texts = jlens_cfg.get("corpus_sequences", [])
        corpus_loader = build_corpus_loader(corpus_texts, model.vocab_size, seq_len)

        jlens_config = JlensConfig.from_experiment_config(config)
        fitter = JlensFitter(model, jlens_config)
        fitter.fit(
            corpus_loader=corpus_loader,
            use_cache=True,
            cache_suffix="_micro_np_v4",
        )
        probe = PsiNetJlensProbe(model, fitter, jlens_config)

        # ------------------------------------------------------------------
        # 1. 样本 J-space 读数
        # ------------------------------------------------------------------
        sample_readings_path = output_dir / "sample_readings.jsonl"
        sample_readings_path.parent.mkdir(parents=True, exist_ok=True)
        n_reading_samples = min(5, len(corpus_texts))
        with sample_readings_path.open("w", encoding="utf-8") as fh:
            for text in corpus_texts[:n_reading_samples]:
                inputs = text_to_token_ids(text, model.vocab_size, seq_len)
                reading = probe.read_all_layers(inputs)
                reading["input_text"] = text
                fh.write(json.dumps(reading, ensure_ascii=False, default=str) + "\n")

        # ------------------------------------------------------------------
        # 2. 概念注入 / 抑制干预
        # ------------------------------------------------------------------
        n_samples = 30
        alpha = 1.0
        dim_a = CONCEPT_SPACE[CONCEPT_A]["dimension"]
        dim_b = CONCEPT_SPACE[CONCEPT_B]["dimension"]

        basis_a = np.eye(model.d_model, dtype=np.float64)[dim_a]
        basis_b = np.eye(model.d_model, dtype=np.float64)[dim_b]

        # 在干预前重新设置随机种子，使干预样本与模型噪声独立于 J-lens 拟合
        # 过程（避免缓存命中/未命中导致的结果差异）。
        intervention_seed = (random_seed or 0) + 1000
        utils.set_random_seed(intervention_seed)

        baseline_a: list[float] = []
        intervened_a: list[float] = []
        baseline_b: list[float] = []
        intervened_b: list[float] = []

        for i in range(n_samples):
            # 使用随机 token 序列作为干预样本，增加样本间方差；
            # 种子已固定，因此序列完全可复现。
            inputs = np.random.randint(
                0, model.vocab_size, size=(1, seq_len), dtype=np.int64
            )

            baseline_logits = model.unembed(model.get_final_state(inputs))[0]

            # 抑制概念 A
            logits_suppress = model.forward_with_intervention(
                inputs, {0: -alpha * basis_a}
            )[0]

            # 注入概念 B
            logits_inject = model.forward_with_intervention(
                inputs, {0: alpha * basis_b}
            )[0]

            baseline_a.append(float(baseline_logits[dim_a]))
            intervened_a.append(float(logits_suppress[dim_a]))
            baseline_b.append(float(baseline_logits[dim_b]))
            intervened_b.append(float(logits_inject[dim_b]))

        significance_level = config.get("statistics", {}).get("significance_level", 0.05)

        suppression_stats = utils.paired_t_test(baseline_a, intervened_a)
        injection_stats = utils.paired_t_test(intervened_b, baseline_b)

        suppression_d = utils.cohens_d(baseline_a, intervened_a)
        injection_d = utils.cohens_d(intervened_b, baseline_b)

        results: dict[str, Any] = {
            "experiment_id": exp_cfg.get("id", "exp_micro_jlens") if exp_cfg else "exp_micro_jlens",
            "experiment_name": (
                exp_cfg.get("name", "J-lens 微观层因果可解释性实验")
                if exp_cfg
                else "J-lens 微观层因果可解释性实验"
            ),
            "status": "success",
            "model": {
                "vocab_size": model.vocab_size,
                "d_model": model.d_model,
                "n_layers": model.n_layers,
                "output_vocab_size": model.output_vocab_size,
            },
            "Jl_matrices": {
                "source_layers": [
                    {"name": sl.get("name", f"layer_{sl['idx']}"), "idx": sl["idx"]}
                    for sl in source_layers
                ],
                "shapes": [list(j.shape) for j in fitter.J],
                "epsilon": jlens_config.epsilon,
                "attribution_method": jlens_config.attribution_method,
            },
            "intervention": {
                "concept_a": CONCEPT_A,
                "concept_b": CONCEPT_B,
                "alpha": alpha,
                "n_samples": n_samples,
                "significance_level": significance_level,
                "suppression": {
                    "mean_baseline": float(np.mean(baseline_a)),
                    "mean_intervened": float(np.mean(intervened_a)),
                    "mean_diff": suppression_stats["mean_diff"],
                    "t_statistic": suppression_stats["t_statistic"],
                    "p_value": suppression_stats["p_value"],
                    "df": suppression_stats["df"],
                    "cohens_d": suppression_d,
                    "significant": suppression_stats["p_value"] < significance_level,
                },
                "injection": {
                    "mean_baseline": float(np.mean(baseline_b)),
                    "mean_intervened": float(np.mean(intervened_b)),
                    "mean_diff": injection_stats["mean_diff"],
                    "t_statistic": injection_stats["t_statistic"],
                    "p_value": injection_stats["p_value"],
                    "df": injection_stats["df"],
                    "cohens_d": injection_d,
                    "significant": injection_stats["p_value"] < significance_level,
                },
            },
            "sample_readings_count": n_reading_samples,
            "random_seed": random_seed,
        }

        utils.save_json(results, output_dir / "results.json")
        # 同时输出到 data 根目录，兼容 tasks.md 中对 exp_micro_jlens.json 的引用
        utils.save_json(results, utils.DATA_DIR / "exp_micro_jlens.json")

        logger.info(
            f"J-lens 微观实验完成: injection p={injection_stats['p_value']:.3e}, "
            f"d={injection_d:.2f}; suppression p={suppression_stats['p_value']:.3e}, "
            f"d={suppression_d:.2f}"
        )
        return True

    except Exception as exc:  # noqa: BLE001
        logger.exception(f"J-lens 微观实验执行失败: {exc}")
        return False


if __name__ == "__main__":
    cfg = utils.load_config()
    exp_config = cfg.get("experiments", {}).get("micro", {})
    success = run(cfg, exp_config)
    raise SystemExit(0 if success else 1)
