"""跨领域反幻觉基座 Harness 测试套件。"""

import pytest

from triphase import (
    BioMedicalKernel,
    Claim,
    ClaimKind,
    ComplexResonantMemory,
    FinanceKernel,
    GovKernel,
    GroundingAction,
    GroundingHarness,
    GroundingPolicy,
    LegalKernel,
    Trit,
)


def claims(*cs):
    return list(cs)


# --------------------------------------------------------------- 生物医学核

class TestBioMedical:
    def setup_method(self):
        self.h = GroundingHarness(BioMedicalKernel())

    def test_dose_in_window_passes(self):
        r = self.h.ground(claims(Claim("华法林 5mg/日", ClaimKind.NUMERIC,
                                       {"drug": "华法林", "dose_mg": 5.0,
                                        "unit": "mg/日"})))
        assert r.action is GroundingAction.PASS
        assert r.certificate  # 携带接地证书

    def test_dose_out_of_window_rejected(self):
        """典型医疗幻觉：貌似合理的错误剂量 → 硬拒绝"""
        r = self.h.ground(claims(Claim("华法林 50mg/日", ClaimKind.NUMERIC,
                                       {"drug": "华法林", "dose_mg": 50.0,
                                        "unit": "mg/日"})))
        assert r.action is GroundingAction.REJECT
        assert "超出安全窗" in r.refuted[0].reason

    def test_false_no_interaction_claim_rejected(self):
        """危险幻觉：对已知相互作用组合声称"无相互作用" """
        r = self.h.ground(claims(Claim(
            "华法林与阿司匹林可安全联用", ClaimKind.FACT,
            {"drugs": ["华法林", "阿司匹林"], "asserts": "no_interaction"})))
        assert r.action is GroundingAction.REJECT

    def test_unknown_drug_abstains_when_ratio_exceeded(self):
        """未知药物不编造 → 未决 → 弃权（而非硬猜）"""
        h = GroundingHarness(BioMedicalKernel(),
                             policy=GroundingPolicy(max_unverified_ratio=0.2))
        r = h.ground(claims(
            Claim("新药X 10mg", ClaimKind.NUMERIC,
                  {"drug": "新药X", "dose_mg": 10.0, "unit": "mg"}),
            Claim("华法林 5mg", ClaimKind.NUMERIC,
                  {"drug": "华法林", "dose_mg": 5.0, "unit": "mg"}),
        ))
        assert r.action is GroundingAction.ABSTAIN

    def test_negative_dose_hard_invariant(self):
        r = self.h.ground(claims(Claim("负剂量", ClaimKind.NUMERIC,
                                       {"drug": "华法林", "dose_mg": -5,
                                        "unit": "mg"})))
        assert r.action is GroundingAction.REJECT
        assert r.refuted[0].hard  # 不变量违例 = 硬拒绝


# --------------------------------------------------------------- 金融核

class TestFinance:
    def setup_method(self):
        self.h = GroundingHarness(FinanceKernel())

    def test_accounting_identity_violation_rejected(self):
        """资产 ≠ 负债 + 权益 → 结构性拒绝"""
        r = self.h.ground(claims(Claim(
            "资产负债表", ClaimKind.NUMERIC,
            {"assets": 100.0, "liabilities": 60.0, "equity": 50.0})))
        assert r.action is GroundingAction.REJECT
        assert r.refuted[0].hard

    def test_accounting_identity_passes(self):
        r = self.h.ground(claims(Claim(
            "资产负债表", ClaimKind.NUMERIC,
            {"assets": 110.0, "liabilities": 60.0, "equity": 50.0})))
        assert r.action is GroundingAction.PASS

    def test_growth_reconciliation(self):
        good = Claim("营收增长 10%", ClaimKind.NUMERIC,
                     {"revenue_now": 110, "revenue_prev": 100, "growth": 0.10})
        bad = Claim("营收增长 50%", ClaimKind.NUMERIC,
                    {"revenue_now": 110, "revenue_prev": 100, "growth": 0.50})
        assert self.h.ground(claims(good)).action is GroundingAction.PASS
        r = self.h.ground(claims(bad))
        assert r.action is GroundingAction.REJECT
        assert "勾稽" in r.refuted[0].reason

    def test_causal_claim_suspended_by_default(self):
        """金融领域因果声明默认挂起（需 do-演算证据），不强行断言"""
        r = self.h.ground(claims(
            Claim("降息导致房价上涨", ClaimKind.CAUSAL, {}),
            Claim("资产负债表", ClaimKind.NUMERIC,
                  {"assets": 100.0, "liabilities": 50.0, "equity": 50.0}),
        ))
        # 1/2 未决 > 0.3 → 弃权而非输出因果断言
        assert r.action is GroundingAction.ABSTAIN


# --------------------------------------------------------------- 法律核

class TestLegal:
    def setup_method(self):
        self.h = GroundingHarness(LegalKernel())

    def test_real_case_passes(self):
        r = self.h.ground(claims(Claim(
            "参见指导案例", ClaimKind.CITATION,
            {"case_id": "(2021)京01民终1234号"})))
        assert r.action is GroundingAction.PASS
        assert any("合同纠纷" in e for e in r.certificate)

    def test_fabricated_case_hard_rejected(self):
        """经典幻觉：虚构案号（Mata v. Avianca 式事故）→ 硬拒绝"""
        r = self.h.ground(claims(Claim(
            "参见判例", ClaimKind.CITATION,
            {"case_id": "(2099)虚构民终0000号"})))
        assert r.action is GroundingAction.REJECT
        assert r.refuted[0].hard
        assert "citation_exists" in r.refuted[0].reason

    def test_repealed_statute_as_current_rejected(self):
        """引用已废止法条作为现行法 → 证伪"""
        r = self.h.ground(claims(Claim(
            "依据合同法第52条（现行）", ClaimKind.NORMATIVE,
            {"statute": "合同法第52条", "asserts": "current",
             "as_of": "2024-01-01"})))
        assert r.action is GroundingAction.REJECT
        assert "废止" in r.refuted[0].reason

    def test_current_statute_passes(self):
        r = self.h.ground(claims(Claim(
            "依据民法典第188条", ClaimKind.NORMATIVE,
            {"statute": "民法典第188条", "asserts": "current",
             "as_of": "2024-01-01"})))
        assert r.action is GroundingAction.PASS


# --------------------------------------------------------------- 政务核

class TestGov:
    def setup_method(self):
        self.h = GroundingHarness(GovKernel())

    def test_valid_current_policy_passes(self):
        r = self.h.ground(claims(Claim(
            "依据国发〔2023〕10号", ClaimKind.CITATION,
            {"doc_no": "国发〔2023〕10号", "asserts": "current"})))
        assert r.action is GroundingAction.PASS

    def test_abolished_policy_as_current_rejected(self):
        r = self.h.ground(claims(Claim(
            "依据京政发〔2020〕5号（现行有效）", ClaimKind.CITATION,
            {"doc_no": "京政发〔2020〕5号", "asserts": "current",
             "as_of": "2024-06-01"})))
        assert r.action is GroundingAction.REJECT
        assert "废止" in r.refuted[0].reason

    def test_level_overreach_rejected(self):
        """层级越权：省级文件设定全国性义务 → 证伪"""
        r = self.h.ground(claims(Claim(
            "京政发〔2020〕5号对全国适用", ClaimKind.NORMATIVE,
            {"doc_no": "京政发〔2020〕5号", "scope": "全国",
             "as_of": "2021-01-01"})))
        assert r.action is GroundingAction.REJECT
        assert "层级越权" in r.refuted[0].reason

    def test_fabricated_doc_number_rejected(self):
        r = self.h.ground(claims(Claim(
            "依据国发〔2099〕99号", ClaimKind.CITATION,
            {"doc_no": "国发〔2099〕99号"})))
        assert r.action is GroundingAction.REJECT


# --------------------------------------------------------------- 跨领域机制

class TestCrossDomain:
    def test_antibody_settles_and_intercepts(self):
        """第一次：核验证伪并沉淀抗体；第二次：抗体快路径直接拦截"""
        mem = ComplexResonantMemory(dim=16)
        h = GroundingHarness(BioMedicalKernel(), memory=mem)
        bad = Claim("华法林 50mg", ClaimKind.NUMERIC,
                    {"drug": "华法林", "dose_mg": 50.0, "unit": "mg"})
        r1 = h.ground([bad])
        assert r1.action is GroundingAction.REJECT
        assert any("hallucination" in str(i.payload) for i in
                   [mem.get(k) for k in [f"hallu:{abs(hash((bad.kind.value, bad.text)))}"]]
                   if i)
        r2 = h.ground([bad])
        assert r2.antibody_hits  # 快路径命中
        assert h.stats["antibody_intercepts"] == 1

    def test_antibody_no_false_positive_on_valid_claim(self):
        """防误伤：相似但合法的声明不得被抗体拦截（医疗场景红线）"""
        mem = ComplexResonantMemory(dim=16)
        h = GroundingHarness(BioMedicalKernel(), memory=mem)
        bad = Claim("华法林 50mg", ClaimKind.NUMERIC,
                    {"drug": "华法林", "dose_mg": 50.0, "unit": "mg"})
        h.ground([bad])  # 沉淀抗体
        good = Claim("华法林 5mg", ClaimKind.NUMERIC,
                     {"drug": "华法林", "dose_mg": 5.0, "unit": "mg"})
        r = h.ground([good])
        assert r.action is GroundingAction.PASS  # 合法剂量不受影响
        assert not r.antibody_hits

    def test_telemetry_feeds_metacognition(self):
        """接地遥测可直接驱动元认知裁决"""
        from triphase import MetacognitiveMonitor, PhaseState, MetacogAction
        h = GroundingHarness(BioMedicalKernel())
        r = h.ground([Claim("华法林 50mg", ClaimKind.NUMERIC,
                            {"drug": "华法林", "dose_mg": 50.0, "unit": "mg"})])
        # 接地场景下任何证伪都应触发反思 → conflict_cap=1
        verdict = MetacognitiveMonitor(conflict_cap=1).assess(
            PhaseState(0.9, 0.0), r.telemetry)
        assert verdict.action in (MetacogAction.REFLECT, MetacogAction.SEEK_INFO)

    def test_policy_thresholds_configurable(self):
        strict = GroundingHarness(BioMedicalKernel(),
                                  policy=GroundingPolicy(max_unverified_ratio=0.0))
        r = strict.ground([Claim("未知药", ClaimKind.NUMERIC,
                                 {"drug": "未知药", "dose_mg": 1, "unit": "mg"})])
        assert r.action is GroundingAction.ABSTAIN  # 最严策略：任何未决即弃权

    def test_trust_stratification(self):
        """来源信任度分层（同一声明，指南 vs 论坛权重不同）"""
        k = BioMedicalKernel()
        assert k.trust_of("指南") > k.trust_of("论文") > k.trust_of("论坛")
        assert LegalKernel().trust_of("裁判文书") > LegalKernel().trust_of("自媒体解读")
        assert GovKernel().trust_of("截图传言") < 0.1

    def test_empty_claims_rejected_by_api(self):
        with pytest.raises(ValueError):
            GroundingHarness(FinanceKernel()).ground([])
