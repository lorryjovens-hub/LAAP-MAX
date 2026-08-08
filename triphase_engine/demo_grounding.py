"""跨领域反幻觉基座 Harness 演示。

同一个 harness，四个领域核，拦截四类典型幻觉：
医疗错误剂量、金融勾稽造假、法律虚构案号、政务失效文件。
"""

import logging

from triphase import (
    BioMedicalKernel,
    Claim,
    ClaimKind,
    ComplexResonantMemory,
    FinanceKernel,
    GovKernel,
    GroundingHarness,
    LegalKernel,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

LINE = "─" * 60


def show(title, report):
    print(f"\n  {title}")
    print(f"    裁决: {report.action.value.upper()}"
          + (f" | 证伪: {report.refuted[0].reason}" if report.refuted else ""))
    if report.action.value == "pass":
        print(f"    接地证书: {report.certificate}")


def main() -> None:
    print("=" * 60)
    print("证明携带生成（PCG）× 四领域核 反幻觉演示")
    print("=" * 60)
    mem = ComplexResonantMemory(dim=16)

    print(f"\n{LINE}\n【生物医学】华法林剂量声明\n{LINE}")
    bio = GroundingHarness(BioMedicalKernel(), memory=mem)
    show("✗ 幻觉：华法林 50mg/日（超窗 5 倍，貌似合理）",
         bio.ground([Claim("华法林 50mg/日", ClaimKind.NUMERIC,
                           {"drug": "华法林", "dose_mg": 50.0, "unit": "mg/日"})]))
    show("✓ 正常：华法林 5mg/日",
         bio.ground([Claim("华法林 5mg/日", ClaimKind.NUMERIC,
                           {"drug": "华法林", "dose_mg": 5.0, "unit": "mg/日"})]))
    show("✗ 危险幻觉：'华法林与阿司匹林可安全联用'",
         bio.ground([Claim("可安全联用", ClaimKind.FACT,
                           {"drugs": ["华法林", "阿司匹林"],
                            "asserts": "no_interaction"})]))
    show("↻ 同一幻觉再次出现 → 负相位抗体快路径直接拦截",
         bio.ground([Claim("华法林 50mg/日", ClaimKind.NUMERIC,
                           {"drug": "华法林", "dose_mg": 50.0, "unit": "mg/日"})]))

    print(f"\n{LINE}\n【金融】报表声明勾稽\n{LINE}")
    fin = GroundingHarness(FinanceKernel())
    show("✗ 幻觉：营收 100→110 却声称增长 50%",
         fin.ground([Claim("营收增长50%", ClaimKind.NUMERIC,
                           {"revenue_now": 110, "revenue_prev": 100,
                            "growth": 0.50})]))
    show("✗ 幻觉：资产100 = 负债60 + 权益50（恒等式不成立）",
         fin.ground([Claim("资产负债表", ClaimKind.NUMERIC,
                           {"assets": 100, "liabilities": 60, "equity": 50})]))
    show("✓ 正常：营收增长 10%",
         fin.ground([Claim("营收增长10%", ClaimKind.NUMERIC,
                           {"revenue_now": 110, "revenue_prev": 100,
                            "growth": 0.10})]))

    print(f"\n{LINE}\n【法律】引用声明验证\n{LINE}")
    law = GroundingHarness(LegalKernel())
    show("✗ 幻觉：虚构案号 (2099)虚构民终0000号",
         law.ground([Claim("参见判例", ClaimKind.CITATION,
                           {"case_id": "(2099)虚构民终0000号"})]))
    show("✗ 幻觉：引用已废止的合同法的第52条作为现行法",
         law.ground([Claim("依据合同法第52条", ClaimKind.NORMATIVE,
                           {"statute": "合同法第52条", "asserts": "current",
                            "as_of": "2024-01-01"})]))
    show("✓ 正常：真实案号",
         law.ground([Claim("参见判例", ClaimKind.CITATION,
                           {"case_id": "(2021)京01民终1234号"})]))

    print(f"\n{LINE}\n【政务】政策文件声明验证\n{LINE}")
    gov = GroundingHarness(GovKernel())
    show("✗ 幻觉：已废止文件当作现行政策",
         gov.ground([Claim("依据京政发〔2020〕5号", ClaimKind.CITATION,
                           {"doc_no": "京政发〔2020〕5号", "asserts": "current",
                            "as_of": "2024-06-01"})]))
    show("✗ 幻觉：省级文件设定全国性义务（层级越权）",
         gov.ground([Claim("省级文件全国适用", ClaimKind.NORMATIVE,
                           {"doc_no": "京政发〔2020〕5号", "scope": "全国",
                            "as_of": "2021-01-01"})]))
    show("✓ 正常：现行国务院文件",
         gov.ground([Claim("依据国发〔2023〕10号", ClaimKind.CITATION,
                           {"doc_no": "国发〔2023〕10号", "asserts": "current"})]))

    print(f"\n{LINE}\n总账\n{LINE}")
    print(f"  生物医学 harness: {bio.stats}")
    print(f"  幻觉抗体库规模: {len(mem)} 条（跨会话复用）")


if __name__ == "__main__":
    main()
