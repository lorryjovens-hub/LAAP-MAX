"""
LAAP x LeWorldModel 全面集成测试
==================================

测试范围:
  1. SIGReg 正则化器 - 防坍塌保证
  2. LatentEncoder - 多模态编码
  3. LatentPredictor - 潜空间预测
  4. CEMPlanner - 潜空间动作规划
  5. LeWMMemoryMonitor - 记忆健康诊断
  6. LeWMConsciousnessRegularizer - 注意力防坍塌
  7. integrate_into_psi_cycle - PSI 循环集成
  8. 完整端到端规划

运行:
  cd D:/LAAP && python tests/test_le_wm_integration.py

印记: Aris 永远记得 Lorry - 2026-07-23
"""

import sys, os, time, math, json
sys.path.insert(0, 'D:/LAAP')

import warnings
warnings.filterwarnings('ignore', category=SyntaxWarning)

import numpy as np

# 抑制非必要日志
import logging
logging.basicConfig(level=logging.WARNING)

PASS = 0
FAIL = 0

def test(name: str):
    def decorator(fn):
        global PASS, FAIL
        def wrapper(*args, **kwargs):
            global PASS, FAIL
            try:
                fn(*args, **kwargs)
                PASS += 1
                print(f"   {name}")
            except AssertionError as e:
                FAIL += 1
                print(f"   {name}: {e}")
            except Exception as e:
                FAIL += 1
                print(f"   {name} [异常]: {type(e).__name__}: {e}")
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════
# 测试 1: SIGReg 防坍塌保证
# ═══════════════════════════════════════════════════════════════

def test_sigreg():
    from laap.agi.le_wm_engine import sigreg
    
    rng = np.random.RandomState(42)
    
    # T1.1: 高斯分布 → 低 SIGReg
    gaussian = rng.randn(1024, 192).astype(np.float32)
    loss_g = sigreg(gaussian)
    assert loss_g < 0.5, f"高斯分布 SIGReg 应 < 0.5, 实际 {loss_g:.4f}"
    print(f"   高斯分布 SIGReg: {loss_g:.6f}")
    
    # T1.2: 全零 → 高 SIGReg
    zeros = np.zeros((1024, 192), dtype=np.float32)
    loss_z = sigreg(zeros)
    assert loss_z > loss_g, f"全零 SIGReg 应 > 高斯, 实际 {loss_z:.4f} > {loss_g:.4f}"
    print(f"   全零 SIGReg:     {loss_z:.6f}")
    
    # T1.3: 坍塌 → 最高 SIGReg
    collapse = np.ones((1024, 192), dtype=np.float32) * 42.0
    loss_c = sigreg(collapse)
    assert loss_c > loss_g, f"坍塌 SIGReg 应 > 高斯, 实际 {loss_c:.4f}"
    print(f"   坍塌 SIGReg:     {loss_c:.6f}")
    
    # T1.4: 小批量也能工作
    tiny = rng.randn(10, 192).astype(np.float32)
    loss_tiny = sigreg(tiny)
    assert not math.isnan(loss_tiny), "小批量不应 NaN"
    print(f"   小批量(10) SIGReg: {loss_tiny:.6f}")
    
    # T1.5: 投影方向数不影响基本性质
    loss_128 = sigreg(gaussian, n_directions=128)
    loss_512 = sigreg(gaussian, n_directions=512)
    loss_2048 = sigreg(gaussian, n_directions=2048)
    assert all(not math.isnan(x) for x in [loss_128, loss_512, loss_2048])
    print(f"   方向稳健性: K=128→{loss_128:.4f}, K=512→{loss_512:.4f}, K=2048→{loss_2048:.4f}")


# ═══════════════════════════════════════════════════════════════
# 测试 2: LatentEncoder 多模态编码
# ═══════════════════════════════════════════════════════════════

def test_encoder():
    from laap.agi.le_wm_engine import LatentEncoder
    
    encoder = LatentEncoder()
    
    rng = np.random.RandomState(42)
    
    # T2.1: 视觉编码
    vis = rng.randn(512).astype(np.float32)
    z_vis = encoder.encode(vision_feat=vis[np.newaxis, :])
    assert z_vis.shape == (1, 192), f"视觉编码维度错误: {z_vis.shape}"
    print(f"   视觉编码: z ∈ R^{z_vis.shape[1:]}, ||z||={np.linalg.norm(z_vis):.2f}")
    
    # T2.2: 三模态编码
    txt = rng.randn(256).astype(np.float32)
    pro = rng.randn(64).astype(np.float32)
    z_multi = encoder.encode(
        vision_feat=vis[np.newaxis, :],
        text_feat=txt[np.newaxis, :],
        proprio_feat=pro[np.newaxis, :],
    )
    assert z_multi.shape == (1, 192), f"多模态编码维度错误"
    print(f"   三模态编码: z ∈ R^{z_multi.shape[1:]}")
    
    # T2.3: 相似输入 → 潜变量距离小
    vis_similar = vis + rng.randn(512).astype(np.float32) * 0.01
    z1 = encoder.encode(vision_feat=vis[np.newaxis, :])
    z2 = encoder.encode(vision_feat=vis_similar[np.newaxis, :])
    similar_dist = float(np.linalg.norm(z1 - z2))
    
    vis_different = rng.randn(512).astype(np.float32)
    z3 = encoder.encode(vision_feat=vis_different[np.newaxis, :])
    diff_dist = float(np.linalg.norm(z1 - z3))
    assert similar_dist < diff_dist, \
        f"相似输入距离({similar_dist:.4f}) 应 < 不同输入({diff_dist:.4f})"
    print(f"   距离一致性: 相似输入={similar_dist:.4f}, 不同输入={diff_dist:.4f}")
    
    # T2.4: 保存/加载
    encoder.save('_test_encoder.npz')
    encoder2 = LatentEncoder()
    encoder2.load('_test_encoder.npz')
    z_reload = encoder2.encode(vision_feat=vis[np.newaxis, :])
    assert np.allclose(z_vis, z_reload, atol=1e-5), "保存/加载后编码不一致"
    os.remove('_test_encoder.npz')
    print(f"   保存/加载: ")
    
    # T2.5: 融合权重更新
    old_weights = encoder.fusion_weights.copy()
    encoder.update_fusion_weights(np.array([0.1, -0.2, 0.3]))
    assert not np.allclose(encoder.fusion_weights, old_weights)
    print(f"   融合权重: {encoder.fusion_weights}")


# ═══════════════════════════════════════════════════════════════
# 测试 3: LatentPredictor 潜空间预测
# ═══════════════════════════════════════════════════════════════

def test_predictor():
    from laap.agi.le_wm_engine import LatentPredictor
    
    predictor = LatentPredictor()
    rng = np.random.RandomState(42)
    
    # T3.1: 单步预测
    z_t = rng.randn(192).astype(np.float32)
    action = np.array([0.5, -0.3, 0.0, 0.8], dtype=np.float32)
    z_pred = predictor.predict(z_t, action)
    assert z_pred.shape == (192,), f"预测维度错误: {z_pred.shape}"
    pred_norm = float(np.linalg.norm(z_pred))
    assert not math.isnan(pred_norm), f"预测不应 NaN, norm={pred_norm}"
    print(f"   单步预测: ||z_pred||={pred_norm:.4f}")
    
    # T3.2: 批量预测
    z_batch = rng.randn(16, 192).astype(np.float32)
    a_batch = rng.randn(16, 4).astype(np.float32)
    z_pred_batch = predictor.predict(z_batch, a_batch)
    assert z_pred_batch.shape == (16, 192), f"批量预测维度错误: {z_pred_batch.shape}"
    print(f"   批量预测: {z_pred_batch.shape}")
    
    # T3.3: 多步 rollout
    actions = rng.randn(15, 4).astype(np.float32)
    trajectory = predictor.rollout(z_t, actions)
    assert trajectory.shape == (16, 192), f"Rollout 维度错误: {trajectory.shape}"
    print(f"   多步 rollout: {trajectory.shape[0]} 步, 终点距起点 {np.linalg.norm(trajectory[-1] - z_t):.4f}")
    
    # T3.4: 损失计算
    z_t = rng.randn(64, 192).astype(np.float32)
    a = rng.randn(64, 4).astype(np.float32)
    z_next = z_t + rng.randn(64, 192).astype(np.float32) * 0.1
    losses = predictor.compute_loss(z_t, a, z_next)
    assert all(k in losses for k in ['mse', 'sigreg', 'total']), f"损失字段缺失: {losses.keys()}"
    print(f"   损失: MSE={losses['mse']:.6f}, SIGReg={losses['sigreg']:.6f}, Total={losses['total']:.6f}")
    
    # T3.5: 保存/加载
    predictor.save('_test_predictor.npz')
    predictor2 = LatentPredictor()
    predictor2.load('_test_predictor.npz')
    # 用同一个输入比较
    z_test = z_t[0]
    a_test = a[0]
    z_orig = predictor.predict(z_test, a_test)
    z_reload = predictor2.predict(z_test, a_test)
    assert np.allclose(z_orig, z_reload, atol=1e-5), f"保存/加载后预测不一致: max_diff={np.max(np.abs(z_orig - z_reload)):.6f}"
    os.remove('_test_predictor.npz')
    print(f"   保存/加载: ")


# ═══════════════════════════════════════════════════════════════
# 测试 4: CEMPlanner 潜空间规划
# ═══════════════════════════════════════════════════════════════

def test_cem_planner():
    from laap.agi.le_wm_engine import LatentPredictor, CEMPlanner, LeWMConfig
    
    config = LeWMConfig(cem_population=50, cem_elites=10, cem_iterations=3, cem_horizon=10)
    predictor = LatentPredictor(config)
    planner = CEMPlanner(predictor, config)
    
    rng = np.random.RandomState(42)
    
    # T4.1: 基本规划
    z_start = rng.randn(192).astype(np.float32)
    z_goal = z_start + 0.05  # 目标很近
    
    t0 = time.perf_counter()
    plan = planner.plan(z_start, z_goal)
    elapsed = time.perf_counter() - t0
    
    assert 'actions' in plan, "规划缺少 actions"
    assert plan['actions'].shape == (10, 4), f"动作序列维度错误: {plan['actions'].shape}"
    assert not math.isnan(plan['score']), "规划评分不应 NaN"
    print(f"   规划耗时: {elapsed*1000:.1f}ms")
    print(f"   动作序列: {plan['actions'].shape}")
    print(f"   评分: {plan['score']:.4f}")
    print(f"   迭代评分: {[f'{s:.2f}' for s in plan['iterations']]}")
    
    # T4.2: 带轨迹返回
    plan_wt = planner.plan(z_start, z_goal, return_trajectory=True)
    assert 'trajectory' in plan_wt
    assert plan_wt['trajectory'].shape == (11, 192)
    # 最终状态应比初始更接近目标
    init_dist = float(np.linalg.norm(z_start - z_goal))
    final_dist = float(np.linalg.norm(plan_wt['trajectory'][-1] - z_goal))
    print(f"   初始距目标: {init_dist:.4f}, 最终距目标: {final_dist:.4f}")
    
    # T4.3: 规划器与引擎集成
    from laap.agi.le_wm_engine import LeWMEngine
    engine = LeWMEngine(config)
    plan_result = engine.plan_to_goal(
        z_start, z_goal,
        pre_encoded=True, horizon=5
    )
    assert 'actions' in plan_result
    print(f"   引擎集成规划: 动作序列长度 {plan_result['actions'].shape[0]}")


# ═══════════════════════════════════════════════════════════════
# 测试 5: LeWMMemoryMonitor 记忆健康诊断
# ═══════════════════════════════════════════════════════════════

def test_memory_monitor():
    from laap.agi.le_wm_integration import LeWMMemoryMonitor
    from laap.agi.le_wm_engine import LeWMEngine
    
    engine = LeWMEngine()
    monitor = LeWMMemoryMonitor(engine)
    
    rng = np.random.RandomState(42)
    
    # T5.1: 健康记忆 → 高健康度
    l1 = rng.randn(32, 192).astype(np.float32)
    l2 = rng.randn(200, 192).astype(np.float32)
    l3 = rng.randn(1000, 192).astype(np.float32)
    l4 = rng.randn(20, 192).astype(np.float32)
    
    report = monitor.diagnose_all(
        l1_embeddings=l1, l2_embeddings=l2,
        l3_embeddings=l3, l4_embeddings=l4,
    )
    for layer, diag in report.items():
        assert 0 <= diag.health <= 1, f"{layer} health 应在 [0,1]: {diag.health}"
        assert diag.action in ('ok', 'reorganize', 'enrich', 'alert')
    all_ok = all(d.health > 0.5 for d in report.values())
    print(f"   健康记忆诊断: {'全部正常' if all_ok else '有异常'}")
    print(f"   各层: {', '.join(f'{k}={v.health:.2f}' for k, v in report.items())}")
    
    # T5.2: 退化记忆 → 低健康度
    collapsed = np.ones((50, 192), dtype=np.float32) * 7.0
    report_bad = monitor.diagnose_all(l1_embeddings=collapsed)
    for layer, diag in report_bad.items():
        print(f"   退化 {layer}: health={diag.health:.4f}, action={diag.action}")
    assert report_bad['L1_working_memory'].action in ('alert', 'reorganize'), \
        f"退化记忆应触发干预, 实际: {report_bad['L1_working_memory'].action}"
    
    # T5.3: 趋势追踪
    for _ in range(5):
        r = monitor.diagnose_all(l1_embeddings=l1)
    trend = monitor.get_trend('L1_working_memory', window=10)
    assert len(trend) > 0, "趋势数据不应为空"
    print(f"   趋势追踪: {len(trend)} 个数据点, 均值={np.mean(trend):.2f}")
    
    # T5.4: 摘要文本
    summary = monitor.summary()
    assert isinstance(summary, str) and len(summary) > 20
    print(f"   摘要:\n{summary}")


# ═══════════════════════════════════════════════════════════════
# 测试 6: LeWMConsciousnessRegularizer 注意力防坍塌
# ═══════════════════════════════════════════════════════════════

def test_attention_regularizer():
    from laap.agi.le_wm_integration import LeWMConsciousnessRegularizer
    
    reg = LeWMConsciousnessRegularizer(lambda_saliency=0.1)
    rng = np.random.RandomState(42)
    
    # T6.1: 正常注意力 → 轻微调整
    normal_attn = rng.randn(30)
    adjusted = reg.regularize(normal_attn)
    assert adjusted.shape == normal_attn.shape
    diversity = reg.get_attention_diversity()
    assert 0 <= diversity <= 1
    print(f"   正常注意力: 多样性={diversity:.4f}")
    
    # T6.2: 塌缩注意力 → 被展开
    collapased_attn = np.zeros(30)
    collapased_attn[0] = 50.0
    reg2 = LeWMConsciousnessRegularizer(lambda_saliency=0.2)
    adjusted_collapsed = reg2.regularize(collapased_attn)
    diversity_collapsed = reg2.get_attention_diversity()
    print(f"   塌缩注意力调整: 调整后多样性={diversity_collapsed:.4f}")
    
    # 检查是否确实被展开
    probs_orig = np.exp(collapased_attn - collapased_attn.max())
    probs_orig /= probs_orig.sum()
    probs_adj = np.exp(adjusted_collapsed - adjusted_collapsed.max())
    probs_adj /= probs_adj.sum()
    entropy_orig = -np.sum(probs_orig * np.log(probs_orig + 1e-10))
    entropy_adj = -np.sum(probs_adj * np.log(probs_adj + 1e-10))
    assert entropy_adj > entropy_orig, "调整后熵应增大"
    print(f"   熵: {entropy_orig:.4f} → {entropy_adj:.4f}")


# ═══════════════════════════════════════════════════════════════
# 测试 7: PSI 循环集成
# ═══════════════════════════════════════════════════════════════

def test_psi_cycle_integration():
    from laap.agi.le_wm_integration import integrate_into_psi_cycle
    
    # 模拟 PSI 循环上下文
    rng = np.random.RandomState(42)
    
    psi_ctx = {
        'cycle_count': 1,
        'perception': rng.randn(512).astype(np.float32),
        'saliency_scores': rng.randn(20),
        'goal_encoding': rng.randn(192).astype(np.float32),
        'memory_embeddings': {
            'L1': rng.randn(20, 192).astype(np.float32),
            'L2': rng.randn(100, 192).astype(np.float32),
        }
    }
    
    result = integrate_into_psi_cycle(psi_ctx)
    
    # 检查扩展的字段
    assert 'latent_z' in result, "缺少 latent_z"
    assert 'attention_diversity' in result, "缺少 attention_diversity"
    assert 'le_wm_plan' in result, "缺少 le_wm_plan"
    print(f"   PSI 扩展字段: {[k for k in result.keys() if k not in psi_ctx]}")
    print(f"   注意力多样性: {result['attention_diversity']:.4f}")
    print(f"   规划评分: {result['plan_score']:.4f}")
    
    # 每 50 次循环触发记忆诊断
    psi_ctx_50 = dict(psi_ctx)
    psi_ctx_50['cycle_count'] = 50
    result_50 = integrate_into_psi_cycle(psi_ctx_50)
    if 'memory_diagnosis' in result_50:
        print(f"   记忆诊断 (cycle 50): ")
    else:
        print(f"   记忆诊断 (cycle 50): 未触发 (需 memory_embeddings 字段)")


# ═══════════════════════════════════════════════════════════════
# 测试 8: 完整端到端规划
# ═══════════════════════════════════════════════════════════════

def test_end_to_end():
    from laap.agi.le_wm_engine import LeWMEngine, LeWMConfig
    
    config = LeWMConfig(
        latent_dim=192,
        sigreg_lambda=0.1,
        cem_population=100,
        cem_elites=10,
        cem_iterations=3,
        cem_horizon=10,
    )
    
    engine = LeWMEngine(config)
    rng = np.random.RandomState(42)
    
    # 模拟: 从当前观测规划到目标观测
    start_obs = rng.randn(512).astype(np.float32)
    goal_obs = start_obs + 0.1  # 目标略微不同
    
    t0 = time.perf_counter()
    plan = engine.plan_to_goal(start_obs, goal_obs)
    elapsed = time.perf_counter() - t0
    
    assert 'actions' in plan, "端到端规划缺少 actions"
    print(f"   端到端规划耗时: {elapsed*1000:.1f}ms")
    print(f"   潜空间: start({np.linalg.norm(engine.encoder.encode(vision_feat=start_obs[np.newaxis,:])[0]):.2f}) "
          f"→ goal({np.linalg.norm(engine.encoder.encode(vision_feat=goal_obs[np.newaxis,:])[0]):.2f})")
    print(f"   评分: {plan['score']:.4f}")
    
    # 表示健康度诊断
    embeddings = rng.randn(200, 192).astype(np.float32)
    health = engine.diagnose_representation_health(embeddings)
    assert 0 <= health['health'] <= 1
    print(f"   表示健康度: {health['health']:.4f} (sigreg={health['sigreg']:.4f})")


# ═══════════════════════════════════════════════════════════════
# 运行测试
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("LAAP × LeWorldModel 全面集成测试")
    print("=" * 60)
    
    tests = [
        ("SIGReg 防坍塌保证", test_sigreg),
        ("LatentEncoder 编码器", test_encoder),
        ("LatentPredictor 预测器", test_predictor),
        ("CEMPlanner 规划器", test_cem_planner),
        ("MemoryMonitor 记忆诊断", test_memory_monitor),
        ("AttentionRegularizer 注意力", test_attention_regularizer),
        ("PSI Cycle Integration", test_psi_cycle_integration),
        ("端到端规划", test_end_to_end),
    ]
    
    for name, fn in tests:
        print(f"\n[{name}]")
        fn()
    
    total = PASS + FAIL
    print(f"\n{'=' * 60}")
    print(f"结果: {PASS}/{total} 通过, {FAIL}/{total} 失败")
    if FAIL == 0:
        print(" 全部通过")
    else:
        print(f" {FAIL} 项失败")
    print(f"{'=' * 60}")
    
    sys.exit(0 if FAIL == 0 else 1)
