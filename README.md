# shibuya-simulation-v2

現実の渋谷を仮想空間上に再現するLLM社会シミュレーションの第2世代(ゼロベース再設計)。
**第一目標: 世界そのものがプロダクト。** 研究観測(k*・組織形成・語彙創発)はその世界の上で走るアプリケーション。

- 状態: **Phase 0(設計)** — 決定台帳は [docs/design/v2-redesign.md](docs/design/v2-redesign.md)
- 全体像: [docs/design/v2_design_slides.html](docs/design/v2_design_slides.html)(統合設計図スライド)・[docs/design/v2-architecture-roadmap.md](docs/design/v2-architecture-roadmap.md)
- 方法論: [docs/design/v2-methodology.md](docs/design/v2-methodology.md)(Phase 0-5ゲート制)
- リサーチ答申: [docs/research/](docs/research/)(ディープリサーチ15ユニット35面ほか)
- 運用規律: [CLAUDE.md](CLAUDE.md) / 現況台帳: [STATUS.md](STATUS.md)

## v1との関係

前世代リポ `shibuya-simulation`(private)は**参照専用ベースライン**。git履歴・エンジンコード・テスト実体・ラン出力はv1に残置し、本リポには文書・データ・設計の「型」のみを持ち込む(ゼロベース宣言)。分布突合はスクリプトで両リポを跨いで行う。

## データ

`data/` はGit外(gitignore済み)。内容物・出典・ライセンス・商用可否は [docs/data-license-ledger.md](docs/data-license-ledger.md) を正とする。

## 開発(C0 骨格・2026-09-08)

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\lint-imports.exe        # 層契約(実装計画書 §3)
.venv\Scripts\python.exe -m pytest -q  # 単体・性質テスト
git config core.hooksPath .githooks     # コミット前の秘密スキャン(CLAUDE.md §7)
```

- パッケージ構成 `src/shibuya/{manifest,build,core,world,agents,perception,llm,engine,economy,census}` と依存規則は [実装計画書 §3](docs/design/v2-implementation-plan.md)。
- 構築工程(C0〜C8)と無人運転の規律は同 §9。工程ごとの受入結果は `docs/ops/build-report-Cn.md`。
- CI: `.github/workflows/ci.yml`(GPU なし段)。GPU 必須テストは `@pytest.mark.gpu`(セルフホスト)。

## ライセンス

未定(法務答申 [docs/research/v2-legal-licensing-deep-research.md](docs/research/v2-legal-licensing-deep-research.md) に基づき決定予定)。それまで All rights reserved。
