# v2小資源検証の方法論リサーチ答申(2026-08-31・Opusサブエージェント・全出典URL付き)

<!-- hdr:v1 -->
- **分野**: 検証とV&V・UQ #22 | **重要度**: P1(親判断・2026-09-15 第191)
- **一次確認**: **D** = **出典 URL なし(2026-09-02 の規律導入前)**=一次確認が丸ごと残る — 出典痕跡 4 件・URL 0 件。09-02 以降の中央値 62 に対して桁が違う
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> ユーザー要件「なるべく少ない計算リソースでも検証ができる仕組み」の設計材料。[事実]/[推測]区別。

## 結論: v2検証ピラミッド推奨設計

| 段 | 体数 | LLM | 所要 | 判定するもの | 上段まで保留 |
|---|---|---|---|---|---|
| L0 mock単体 | 1-10 | stub決定的 | **10分以内**(Ten-Minute Build) | 契約・状態遷移・パース・凍結照合 | 振る舞い品質すべて |
| L1 縦切り | 数百 | mock主+golden 25-50件実LLM | 数分〜十数分 | 機構の配線・シード再現・golden±3%回帰 | 集計量の水準・分布形 |
| L2 縮小渋谷 | 1万(N系列2.5k/5k/10k) | 実LLM(本番と同系列) | 数時間 | **条件間の相対差とN依存曲線**・早期警戒信号・性能/RSS予算 | 絶対水準の較正・創発の有無 |
| L3 本番 | 40万 | 実LLM | 本番 | 創発の確認・絶対水準 | — |

**規模外挿の規律(必須化推奨)**: ①単一Nの数値を成果物にしない=N系列(最低3点等比)+N^(-1/2)参照線
②「率」(線形に縮めてよい)と「容量・閾値」(縮めてはいけない)をconfタグで分離宣言
③各機構をglobal/community/local feedに宣言し、**globalのみ「L2合格=L3合格」・community/localはL2では棄却のみ可**
④N依存が疑われる較正パラメータは「N非依存の証拠」を要求 ⑤創発の有無は小規模で判定しない(陰性=「N₀で未検出」
のみ・予兆=分散/自己相関を測る)⑥希少事象はL2で0回=情報ゼロ・上限信頼区間(3/N則)だけ記録して上段へ。

## 主要な事実

**交通(MATSim)**: 10%人口サンプルがBerlin/Zurich/Parisの標準・**flow capacityは線形縮小可だがstorage capacityは
不可**(開発陣明言・25%ならflow0.25/storage0.5がbest practice)・**10%未満では平均統計量すら信頼できず25%以上で
主要統計が保存**・収束反復数自体が規模依存(Llorca&Moeckel=縮小系は「速く収束する別世界」)。
→[推測] 40万体に対する1万体=2.5%は「平均も信頼できない」帯=**絶対量較正には使えず、機構の生存確認と
相対比較に用途限定**。

**疫学(Covasim)**: rescale=True既定(感受性残5%で非感受性を再サンプルし1体=k人へ格上げ)=「情報が乗る部分集合
だけ実体化」。**最大の落とし穴=単一サイズではdensity/frequency-dependentの区別がつかず(パラメータで吸収)、
規模の異なる系で予測が分岐**(Sci Rep 2022)=「縮小系で較正したパラメータが大規模で壊れる」の最明快な定式化。
合成人口生成器を縮小段と本番段で共有するのが実務の要点(EpiCast 2.0)。

**有限サイズスケーリング**: data collapse(N系列の曲線を1本に重ねる)がABMにも適用実績(Minority Game・意見動学)。
二段構えの先行=(a)早期警戒信号(critical slowing down=分散・自己相関上昇・安価)(b)sequential bifurcation
(92因子を19組合せで10因子に絞る)。

**LLM縮約(直撃先行)**: **Poor Man's Agentic Modeling(arXiv 2608.11215)**=LLMエージェントを2-12パラメータ代理に
置換しN=20〜3,200+をラップトップで。中核=[interaction order×memory]分類で**代理誤差のN依存を実行前に予測**:
- global feed(全体集計を見る)→誤差N^(-1/2)減衰=代理有効
- community feed(ブロック内共有)→誤差O(1)頭打ち=block-aware closure要
- local feed(グラフ近傍)→**誤差がNとともに増大しうる**=pair approximation要
[推測] v2への含意: 噂拡散・SNS・関係ネットワークはcommunity〜local寄り=小規模検証の誤差が縮まらない側。
人流集計を見る層はglobal=小規模検証が正当化される。

**小モデル代理の限界**: 推論は7B超で安定する創発挙動・逆スケーリング実在(大が小を28.4pt下回る例7.7%)
→**「小で通れば大でも通る」も「小で落ちれば大でも落ちる」も成立しない**。

**LLMテスト実務**: fake/mockで決定的経路検証+golden dataset(25-50件から・毎PR CI・主要指標±3%劣化でビルド失敗)
+ReplayLLMClient(トレース記録の決定的再生)・費用最適順=決定的チェック→ヒューリスティック→LLM judge。

**SW工学**: テストピラミッド(Fowler)・XP Ten-Minute Build・ゲーム業界=固定シードRNG+入力記録リプレイ+
smoke/nightly分離。

## 落とし穴一覧

①容量の線形縮小=渋滞過剰生成 ②縮小系チューニング=別世界の最適化 ③機構の同定不能性(density/frequency)
④希少事象・創発の偽陰性(OASIS herd=100体で不在・1万体で出現)⑤局所相互作用で縮約誤差がN増大
⑥モデル複雑度の小増加→較正データ要求の大増加。
[推測]定式化: **小規模合格は必要条件であって十分条件ではない**。合格が保証するのは「機構がN₀で壊れない」
ことだけ。N依存未測定の量への外挿は無効。小規模の不合格も機構バグと有限サイズ効果の区別なしには棄却根拠にならない。

## v1資産の再利用

6,782テスト群=そのままL0/L1基盤(契約列挙ピン・凍結照合は移植価値大)/mock駆動→Replay型へ拡張し
**v1実LLMログをgolden traceとして凍結**が最安の投資/同一Nで最低3seed必須化(seed分散とN効果の分離)/
v1の1万体較正値はcommunity/local機構についてL3再測定が必要な暫定値へ格下げ推奨。

## 主要出典

MUM25 paper30・MATSim-users ML(flow/storage)・Ge+(2008.04762)・Llorca&Moeckel(Procedia CS 151)・
Covasim parameters.py+Kerr+(PLOS CB 2021)・Sci Rep 2022(s41598-022-26552-w)・Ferrari+(PMC3062980)・
PMC5156435・EpiCast 2.0(2504.03604)・autoScale.py(0910.5403)・FSS意見動学(2606.05349)・
Scheffer+(Nature 2009)・Kleijnen sequential bifurcation・**Poor Man's Agentic Modeling(2608.11215)**・
創発7B(2509.21013)・Inverse Scaling(2306.09479/2604.00025)・Agiflow/DEV/Braintrust(LLMテスト実務)・
Fowler Test Pyramid・Agile Alliance XP・iXie(ゲームQA)・OASIS(2411.11581)・較正データ要求
(Env Modelling&Software)。(URLはリサーチ実行ログに完全版)
