# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **1 / 10**
> 第1〜第180(2026-09-01〜09-14)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第181 ユーザーの問い「v1 でリサーチしていた分野が見れるか・リストアップ」→ v1 資産の照合(2026-09-14)

- **v1 リポ(参照専用)の docs/ を親が実読**して数えた: `docs/research/` **160 本**(うち 33 は v2 答申の初出=v1 固有は **127 本**)・`docs/lit/` **44 本**(1 論文 1 メモ・主張/機構/効く seam/批判の定型)・`docs/references.md`(クラスタ別の読書リスト)・**`docs/research-scope.md`=分野選定と実装重要度の地図そのもの**(v0.1・P0/P1/P2)。
- **v1 の分野マップ**: Object / Method / 経済・制度・基盤 / 生命・ビジョン の 4 群。**P0 の 8 分野**= 性格・動機づけ心理学 / 集合行為・社会運動論 / 文化進化・社会言語学 / ネットワーク科学・拡散理論 / 複雑系・自己組織化 / マルチエージェント AI・ABM / 計測・心理測定 / 制度経済学・ガバナンス。第2フェーズで Lynch(都市)・Searle(社会存在論)・Gibson/Tolman(環境知覚)・PLATEAU 可視化・分散システム(actor)が P0 昇格。「世界2.0 の 30 分野」を均等に一巡済み(群①substrate/②engagement/③build・viz/④哲学)。
- **選定が違う理由=上位の問いの差**: v1 は「世界改変者(agency)の創発は規模のどこで起きるか(k* 相転移)」・v2 は「現実の渋谷をどこまで再現でき どう検証するか」。v1 は創発を測る分野が厚く、v2 は現実に釘付けする分野が厚い。
- **第180 で見つけた「答申が無い 4 分野」に v1 の素材があるか**を照合: **社会ネットワーク科学=使える**(lit/network__diffusion-overview に Centola & Macy 2007 complex contagion・Granovetter 1978 閾値・Watts 2002 cascades。ただし「ラベルと運動の伝播」文脈からの読み替えが要る)/**UQ=部分的**(uncertainty-audit は「シム内の揺らぎの監査」で、要るのは「入力誤差の伝播」=別物だが出発点)/**科学哲学=部分的**(measurement__validation-overview に operational validity・LLM-judge の循環・face validity の限界)/**物質フロー分析=ほぼ無い**(新規リサーチ)。
- **前倒しできる発見**: v1 の `lit/measurement__validation-overview.md` が Larooij & Törnberg「Validation is the central challenge」(AI Review 2025)を既に出典にしている。これは有志まとめ #11・残務台帳 R-2 の「本文実読が残る」項。**v1 に読解メモがある**ので R-2 の一部は v1 の再読で済む。
- 記録: [v2-discipline-map.md](../research/v2-discipline-map.md) §6 に付録として追記(v1 の 127 本の分野内訳 12 束つき)。**提案 3 件(未実施)**: ①v1 答申の棚卸しを残務台帳へ ②社会ネットワーク科学は v1 の読み替えから始める ③第2陣の文献メモは v1 の `lit/` の短い定型に戻す。
- **次**: ユーザー判断(M1〜M4・holdout 開封・c7-day-5・A5・A6・リサーチの着手順・上の提案 3 件)。
