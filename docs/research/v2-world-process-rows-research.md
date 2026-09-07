# D-R2-3 リサーチ答申: エンジン/LLM線引き16行の詳細決定材料

> **親検収(Fable・2026-09-06)**: 出典を親が一次確認した。✔=親が実読して数値一致。
> - ✔ Fish, Gonczarowski & Shorrer 2024(arXiv 2404.00806 HTML実読): 「LLM-based pricing agents quickly and autonomously reach supracompetitive prices and profits」・実験環境の価格上限=独占価格の2.34倍(試行ごとにU(1.5,2.5)から抽選)・複占300期。
> - ✔ EconAgent(arXiv 2310.10436 HTML実読): 価格 P←P(1+φ_P), φ_P〜sign(φ̄)U(0, α_P|φ̄|)・α_P=0.10/賃金 α_w=0.05/LLMは労働性向p^w(Bernoulli)と消費性向p^c∈[0,1]のみ。
> - ✔ Roblox Marketplace公式(実読): 「the more an item is priced above its asset type's price floor, the greater the share of revenue the creator earns」逐語一致。**導入日2024-02-22・フロア例(75/175/2 Robux)・手数料30%はこのページに無い=別ページ由来・親未確認**。
> - ✔ Lindenfors, Wartel & Lind 2021(PMC実読): ベイズ推定69.2-108.6・GLS 16.4-42.0・95%CI 4-520/2-336・「'Dunbar's number' is a concept with limited theoretical foundation lacking empirical support」。
> - ✔ 東京都最低賃金(台東区公式実読): 「令和7年10月3日より1,226円」。
> - ✔ 警察庁『令和6年の犯罪情勢』(PDF実読): 刑法犯検挙率38.9%・重要犯罪86.5%・重要窃盗犯55.7%。✔ Saramäki et al. 2014 PNAS(PDF実読): 上位20人のJaccard入替を確認(数値は答申の抽出どおり)。✔ Goel et al. 2016(PDF実読): 「over 99%—are tiny and terminate within a single generation」「0.025% of diffusion trees containing at least 100 nodes」。
> - GA(α=1・0.995・閾値150「in our implementation」・2-3回/日)は本日別答申で親確認済み。**注**: 行15の「反省80-120万呼(20-30%)」はGAの2-3回/日を掛けた試算。契約書§6で日次内省=就寝同期1.05回/日(42万呼=10.5%)を決定済みなので、この費目は既に解消されている。
> - 空欄8項目(LLM価格の桁外れ頻度の直接報告・AI Town系・Ebbinghaus代表値・渋谷の実店舗席数・暗数調査の罪種別申告率・辺更新規則の先行実装・最低賃金2026改定・行13/14先行研究)は答申の申告どおり。
> - 正典化: docs/research/v2-world-process-rows-research.md(D-R2-3の根拠)。


作成: 2026-09-06 / レーンD / リサーチサブ(Opus 5) / 親検収前の草案

**確認状況の凡例**: `✔✔` = PDFを手元で原文抽出しキーワード一致を目視(逐語引用の信頼度が最も高い) / `✔` = WebFetchまたは検索の要約経由(引用文は小モデル経由のため親の一次確認を推奨) / `空欄(未確認)` = 今回確認できず、記憶では埋めない。

---

## 要約(10行)

1. **行5 価格形成の最大論点に決着材料あり**: LLMに価格を自由に出させると**供給競争価格を超える水準へ自律収束する**(Fish+2024、RL版はCalvano+2020 AERで既知)。しかも実験系自身が「独占価格の2.34倍」という**環境側の上限を課している**=先行研究も素の自由価格を許していない。
2. 対照的に **EconAgent(ACL2024)はLLMに価格を出させない**。価格・賃金は需給不均衡に比例するエンジン規則(α_P=0.10, α_w=0.05)で、LLMは労働性向・消費性向の[0,1]スカラーのみ。→ 提案案#14「内生フロア+逸脱比例コスト」は**この2極の中間**として正当化できる。
3. LLMの選択自体は経済合理性が高い(GPTのGARP違反ほぼ無し・CCEI 0.997-0.999、人間より高い)が、**言語フレームに敏感**=桁外れは「無能」でなく「プロンプト感応」由来。対策はフロア/キャップ+スカラー出力+相対倍率化。
4. **行6 賃金は行5と同型で成立する**。制度フロアは東京都最低賃金1,226円/時(2025-10-03発効)が使える(等級A)。ただし日本の名目賃金の下方硬直は**1998年以降ほぼ消失**(Kuroda&Yamamoto)ので「硬い下限=最低賃金のみ、下方硬直は弱いペナルティ」が妥当。
5. **行8 Dunbar 150は根拠等級Cに落とすべき**。Lindenfors+2021が同じ回帰から69-109/16-42を導き統計的支持を否定。入替率は実測あり(Saramäki+2014: 6か月間隔のJaccard 0.22-0.27、上位5人でも0.39)。
6. **行9 SNSはO(feed_size)増分で十分**。拡散の99%超は単世代で終わる(Goel+2016)、100ノード以上のカスケードは全体の0.025%(約4,000本に1本)。「バイラル」より「大きな一斉配信」が支配。
7. **行15が予算の最大費目**。GAの反省頻度(1日2-3回)を40万体に素直に掛けると80-120万呼=**400万呼予算の20-30%**。減衰・retrievalは完全エンジン、反省はトリガ閾値で強く絞るのが必須。
8. **行16は「LLM提案→エンジンのスキーマ検証」**の3層(既存動詞へのマッピング/パラメータ拡張/新動詞検疫)。先行例はVoyagerのスキルライブラリ(実行可能コード+自己検証)とPDDL/STRIPSの前提条件・効果スキーマ。
9. **行12は二段確率で組める(等級A)**。令和6年の刑法犯検挙率38.9%、重要犯罪86.5%、重要窃盗犯55.7%(警察庁・原文抽出)。暗数側は「被害申告率は罪種で差、平成20年調査ではいずれも50%以下」。P(立件)=申告率×検挙率。
10. **行2の現実値は等級Dどまり**。回転率(ファストフード20回/レストラン・居酒屋2-3回/フルコース1回)・客席稼働率65-70%は業界記事が出所で、渋谷の実店舗席数は**空欄(未確認)**。

---

## 問い1: 行5 価格形成 — LLMに価格を提案させた先行研究と推奨運用形

### (a) 価格逸脱の大きさ・桁外れの頻度

**直接に「桁で外す頻度」を報告した論文は今回見つからなかった=空欄(未確認)。** 代わりに以下2点が実務上の代理指標になる。

- **環境側が上限を課すのが標準実務**。Fish, Gonczarowski & Shorrer (2024) の寡占実験では、価格上限を **「2.34⋅p^M, where the number 2.34 was drawn from Unif([1.5,2.5])」**(独占価格 p^M の2.34倍、係数は一様分布から抽選)に設定し、限界費用は **「c_i=1」**。✔(WebFetch要約経由・原文の逐語性は要一次確認)
  → **含意**: 先行研究ですら「LLMの生の価格出力」を無制限には許していない。上限は独占価格の1.5-2.5倍という**桁ではなく倍率オーダー**で置かれている。当プロジェクトの「内生フロア+逸脱比例コスト」は同じ発想の下側版。
  出典: https://arxiv.org/abs/2404.00806 / HTML: https://arxiv.org/html/2404.00806v5

- **選択の合理性そのものは高い**。Chen, Liu, Mazumder ら "The emergence of economic rationality of GPT" (PNAS, 2023) は予算制約下の選択でGARP違反を測り、**「95, 89, 81, and 92 out of 100 GPT observations for risk, time, social, and food preferences exhibit no violations of GARP」**、**CCEI平均が 0.998/0.997/0.997/0.999(人間は 0.980/0.985/0.967/0.963)**。ただし **「sensitive to contexts based on the language frames of the choice situations」**。✔(検索要約経由)
  → **含意**: 桁外れの主因は推論能力ではなく**プロンプト/フレーム感応**。したがって対策は「賢いモデルにする」ではなく「**出力形式を固定し、参照アンカーを必ず添える**」。
  出典: https://www.pnas.org/doi/10.1073/pnas.2316205120 / https://arxiv.org/abs/2305.12763

### (b) 共謀/硬直の出現

- **LLMでも出る**。Fish+2024 要旨(逐語): **「We conduct experiments with algorithmic pricing agents based on Large Language Models (LLMs). In oligopoly settings, LLM-based pricing agents quickly and autonomously reach supracompetitive prices and profits.」** さらに **「variation in seemingly innocuous phrases in LLM instructions ('prompts') substantially influence the degree of supracompetitive pricing」**、要因として **price-war concerns**(値下げ戦争の懸念)を同定。結果はオークション設定にも及ぶ。✔
- **プロンプト前置きの効果は統計的に大**: Prompt Prefix P1(長期利潤最大化を強調)は P2(「競合より安くすれば通常より多く売れる」+攻撃的選択肢への言及)より **「typically results in substantially higher prices (p<0.00001)」**。✔(WebFetch要約経由・要一次確認)
- **LLM以前から既知**。Calvano, Calzolari, Denicolò & Pastorello (2020) *AER* 110(10): 3267-97: Q学習エージェントが**通信なしに supracompetitive price を学習**し、**有限の懲罰局面→段階的協調復帰**という共謀戦略で維持。コスト・需要の非対称、プレイヤー数、各種不確実性に頑健。✔
  出典: https://www.aeaweb.org/articles?id=10.1257/aer.20190623

- **現実側の硬直の基準値**: 日本の価格改定頻度は**月次で約20%**(=平均持続 約5か月)。「The average frequency of price changes is approximately 20% on a monthly basis」、加えて「frequency of price changes is more heterogeneous than in the US」「Large cities tend to have a higher frequency of price changes」。✔(検索要約経由。出所は東大CARF WP F570 / *The Japanese Economic Review*)
  出典: https://www.carf.e.u-tokyo.ac.jp/wp/wp-content/uploads/2023/09/F570.pdf / https://link.springer.com/article/10.1007/s42973-024-00161-w
  → **含意**: 渋谷シムで店舗が毎日価格を動かしたら**現実の5倍以上に硬直不足**。価格提案の呼び出し頻度そのものが較正対象(下記案の頻度パラメータ)。

### (c) 対策の実証(フロア/キャップ・アンカー・スカラー出力)

| 対策 | 実証の有無 | 出所 |
|---|---|---|
| 価格キャップ(環境強制) | Fish+2024が実際に採用(2.34×独占価格) | ✔ arXiv 2404.00806 |
| プロンプト前置きの統制 | 効果が有意(p<0.00001) | ✔ 同上 |
| スカラー出力([0,1]の性向値・刻み0.02) | EconAgentが採用。JSONで `'work'`/`'consumption'` を **「a value between 0 and 1 with intervals of 0.02」** | ✔ arXiv 2310.10436 |
| **動的フロア + 逸脱に応じた累進レベニューシェア** | **商用実装として実在**: Roblox が 2024-02-22 に Marketplace へ dynamic price floor を導入(市況で通常日次変動)。**「the more an item is priced above its asset type's price floor, the greater the share of revenue the creator earns」**(累進レベニューシェア)。アクセサリのマーケット手数料は30%。フロア例: UGCヘッド75 Robux / フルボディ175 Robux / クラシックTシャツ2 Robux。✔(公式は https://create.roblox.com/docs/marketplace/marketplace-fees-and-commissions 、フロア値はFandom wiki経由=**要一次確認**) |
| アンカー提示(原価・競合価格・前期価格を必ず添える) | 直接の対照実験は**空欄(未確認)**。ただしGPTのフレーム感応(PNAS 2023)から間接支持 |

**注意: Roblox方式は当プロジェクトの提案#14と符号が逆**。Robloxは「フロアから**上に**離れるほど創作者の取り分が**増える**」(高価格を奨励=デフレ防止のsink設計)。当方の案#14は「フロアから離れるほど**コストが増える**」(逸脱抑制)。**同じ機構の符号違い**なので、どちらを採るかはユーザー決定事項。前者は価格の上方創発を促し、後者は保存則と体感物価の安定を優先する。

### 推奨運用形: 3案比較

前提の呼数基礎: 店舗POI **2,337**、予算 **400万呼/シミュ日**(=40万体で1体10呼/日)。

| | **A案: 内生フロア+逸脱比例コスト(提案#14)** | **B案: エンジン全決定+LLMは3値提案(EconAgent型)** | **C案: LLM自由価格+上限のみ(Fish型)** |
|---|---|---|---|
| LLMの出力 | 相対倍率スカラー `r ∈ [0.7, 3.0]`(フロア価格に対する倍率) | `{値上げ / 据置 / 値下げ}` の3値 + 強度[0,1] | 絶対価格(円) |
| エンジンの役割 | フロア `p_floor = 原価 × k`(k=業態別係数)を毎tick再計算 / 成立価格 `p = p_floor × r` / 逸脱コスト `fee = β·(r−1)²·売上` を sink 登録 | `P ← P(1+φ_P), φ_P ~ sign(φ̄)·U(0, α_P·|φ̄|)`, `φ̄=(D−G)/max(D,G)`, α_P=0.10。LLMは φ̄ の符号を上書きできるだけ | 上限 `p ≤ κ·p^M`(κ~2.0)のみ |
| **保存則整合** | ◎ 逸脱コストが**明示的sink**として台帳に載る。原価×係数のフロアは faucet 側と独立。残差科目に落ちない | ◎ 価格は状態変数、取引は保存。LLMは分布を歪めるだけ | △ 上限外・負値・桁外れの棄却処理が**残差科目に流れやすい**。棄却時のフォールバック価格が事実上の設計者指紋になる |
| **呼数** | 2,337店 × 1回/日 = **2,337呼**(予算の0.06%)。1時間ごとでも 56k(1.4%) | 同上(むしろ同額)。ただしLLM無しでも回るので 0 呼まで落とせる | 同上 |
| **創発余地** | ◎ 倍率は連続量。値下げ競争・便乗値上げ・高級路線がすべて表現可能。共謀もフロア上で観測可能(=観察対象として残る) | △ 3値では価格帯の分化が起きにくい。EconAgentが100体・240か月で回した設計であり、業態分化の観察には粗い | ◎ 最大。ただし供給競争価格超えへの自律収束(Fish+2024)が**そのまま起きる**ので「創発」か「LLM由来のアーティファクト」かの識別が困難 |
| **expedient宣言** | フロア係数 k と逸脱コスト係数 β が expedient。**感度試験必須**(β=0 で価格分布・物価指数がどれだけ壊れるかを示す) | α_P=0.10 が expedient(EconAgent由来の慣行値) | κ が expedient |
| **現実照合(パターン台帳ゲート)** | 月次経済センサスの物価指数 + 価格改定頻度(現実 ~20%/月)で照合可 | 同左だが分化が出ないため店舗別価格分散が照合できない | 照合可だが共謀由来の高止まりが混入 |

**推奨: A案(内生フロア+逸脱比例コスト)を第1陣、C案をablation対照として1回だけ回す。**
理由: (1) 呼数が予算の0.06%と無視できるのでLLMを噛ませる価値がある、(2) 逸脱コストを sink として登録すれば保存則運用②(faucet/sink全登録)に自然に収まる、(3) Fish+2024が示す「素の自由価格は超競争価格へ収束する」を回避しつつ、フロア上の相対倍率という形で共謀・値下げ競争の**観察**は保持できる。
**追加の必須ゲート**: 価格提案の**呼び出し頻度**そのものを較正対象にすること。現実の日本は月次改定頻度~20%なので、店舗が毎tick価格提案すると硬直不足になる。第1陣は「1日1回提案・ただしエンジンが確率0.2/月でしか反映しない」等の**改定確率ゲート**(Calvo型)を推奨。【推測】この確率値は月次価格改定頻度20%から直接較正できる。

---

## 問い2: 行6 賃金 — 行5と同型が成り立つか

### 結論: 成り立つ。ただしフロアの性格が違う。

- **同型性の先行例**: EconAgent は価格と賃金を**完全に同じ形の規則**で動かしている。賃金: **「w_i ← w_i(1+φ_i), φ_i ~ sign(φ̄)U(0, α_w|φ̄|)」** で **α_w = 0.05**、価格側は **α_P = 0.10**。不均衡は **「φ̄ = (D−G)/max(D,G)」**。✔(WebFetch要約経由・要一次確認)
  → 賃金の調整率が価格の**半分**に設定されている(0.05 vs 0.10)=**賃金の方が粘着的**という前提が既に慣行値として存在する。これはそのまま行6の初期値に使える(等級C)。
  出典: https://aclanthology.org/2024.acl-long.829/ / https://arxiv.org/abs/2310.10436

### 制度フロアとしての東京都最低賃金

- **東京都最低賃金 1,226円/時、令和7年10月3日発効**(引上げ額63円)。✔ 台東区公式ページで確認: 「東京都の最低賃金は、令和7年10月3日より1,226円になりました」。 https://www.city.taito.lg.jp/bunka_kanko/koyo_shugyo/jigyousya/2025tokyo_saichin.html
- **2026年度改定は答申段階で1,280円(+54円)との情報があるが、出所が非公式サイトのため 空欄(未確認)**。厚労省・東京労働局の公式発表を親が一次確認すること。
- **妥当性の評価**: ◎ **等級A**。理由: (1) 単一の公的数値で全時給労働に一律適用、(2) 発効日が明示されているので**シミュレーション内の制度ショック実験**(最低賃金引上げ)にそのまま使える、(3) faucet/sink の議論に入らない純粋な制約(=保存則を汚さない)。
  → **行5のフロアが「原価×係数」という内生量(expedient)なのに対し、行6のフロアは外生の公的数値(mechanism)**。この非対称は設計上の強みなので明記すべき。

### 日本の賃金硬直性 — 「下方硬直を硬い制約にしてはいけない」

- Kuroda & Yamamoto (BOJ/IMES) の一連の研究: **事業所集計データで、フルタイム労働者の名目賃金の下方硬直は1997年まで観察されるが、それ以降は消失**。**パートタイム女性の時給はほぼ完全に下方硬直**する一方、**フルタイムの所定内月給・年収の下方硬直は限定的**。日本の名目賃金は米国・スイスと比べ**下方硬直がかなり弱い**。✔(検索要約経由)
  出典: https://www.imes.boj.or.jp/research/papers/english/03-E-03.pdf / https://www.imes.boj.or.jp/research/papers/english/me25-2-2.pdf
- **現在の賃上げ環境**: 連合2025年春闘最終集計で賃上げ率 **5.25%**(1991年の5.66%以来34年ぶり高水準、2年連続5%超)。ベア・定昇を分離できる3,594組合ではベア平均 **3.7%**。中小に限ると **4.65%**。✔(検索要約経由・出所は連合最終集計を報じた日経/時事/JILPT)
  出典: https://www.jil.go.jp/kokunai/blt/backnumber/2025/07/shuzai_01.html

**推奨(行6)**:
- 硬いフロア = 最低賃金(時給、外生・日付つきで改定)。**mechanism**。
- 下方硬直 = **弱いペナルティ**として実装(名目賃下げ提案に対し離職確率を上げる/コストを課す)。硬い禁止にしない。**expedient**・感度試験対象。Kuroda&Yamamoto が「1998年以降は硬直が消失」と示している以上、硬い禁止は現実に反する。
- 年次のベースアップは**組織単位で年1回のLLM提案**(1.1万組織 × 1回/年 ≒ 30呼/日相当、予算の0.001%)。第1陣で入れても呼数コストはゼロに等しい。

---

## 問い3: 行8 社会関係グラフ

### (a) 辺の上限 — Dunbar層の実証と批判

**支持側**: Zhou, Sornette, Hill & Dunbar (2005) *Proc. R. Soc. B* 272(1561): 439-444。フラクタル解析により、**スケーリング比が約3の離散階層**を高い統計的信頼度で同定。**「humans spontaneously form groups of preferred sizes organized in a geometrical series approximating 3–5, 9–15, 30–45, 90–140, 250–400」**。✔(検索要約経由)
出典: https://royalsocietypublishing.org/doi/10.1098/rspb.2004.2970 / DOI: 10.1098/rspb.2004.2970

**層の機能名**(Dunbar 2020, *Proc. R. Soc. A* 476): support clique(5) / sympathy group(15) / affinity group(50) / full active network(150) / acquaintances(500) / 1500。✔(検索要約経由・機能名の記述は二次資料由来のものを含むので**要一次確認**)
出典: https://ora.ox.ac.uk/objects/uuid:f56e97cb-c481-449c-b792-a76156550d9e/download_file?safe_filename=DunbarVoR2020.pdf / PubMed: https://pubmed.ncbi.nlm.nih.gov/32922160/

**批判側(重要)**: Lindenfors, Wartel & Lind (2021) *Biology Letters* 17(5): 20210158, "'Dunbar's number' deconstructed"。**同じ新皮質-群サイズ回帰から出発しても、手法によって全く違う数字が出る**: **「Bayesian and generalized least-squares phylogenetic methods generated approximations of average group sizes between 69–109 and 16–42, respectively」**。150という特定値に統計的支持はない、が結論。✔(検索要約経由)
出典: https://royalsocietypublishing.org/doi/abs/10.1098/rsbl.2021.0158 / DOI: 10.1098/rsbl.2021.0158 / PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC8103230/

→ **設計含意**: 150という上限は **根拠等級C(先行実装の慣行値)** に落とすべきで、A/Bを主張してはいけない。**expedient宣言が必須**。感度試験は「上限を 50 / 150 / 500 で振っても社会現象(情報拡散速度・階層形成)が定性的に変わらないこと」を示す形。

### (b) 現実の関係入替率 — 実測値(原文抽出済み)

**Saramäki, Leicht, López, Roberts, Reed-Tsochas & Dunbar (2014) PNAS 111(3): 942-947.** ✔✔ (PDFから原文抽出・逐語)

- 対象: **24名**の学生を**18か月**追跡(高校→大学/就職の移行期)。携帯通話記録+質問紙。
- 全ネットワークの入替(6か月区間どうしのJaccard指数):
  > **「For the entire networks of participants, ⟨J(I1,I2)⟩ = 0.22 ± 0.09 and ⟨J(I2,I3)⟩ = 0.27 ± 0.09.」**
- 上位20人:
  > **「the Jaccard indexes for the top 20 ranking alters are ⟨J(I1,I2)⟩ = 0.36 ± 0.13 and ⟨J(I2,I3)⟩ = 0.44 ± 0.10」**
- 上位5人:
  > **「for the top 5 ranking alters are ⟨J(I1,I2)⟩ = 0.39 ± 0.23 and ⟨J(I2,I3)⟩ = 0.39 ± 0.22」**
- 「ここでの入替には、上位20位/5位から下に落ちたalterも含む」旨の注記あり:
  > **「Note that here, turnover includes alters dropping in rank below the top 20 or top 5.」**
- 通信量の集中: 女性(男性)で最上位alterへの通話割合が平均 **0.25±0.08(0.20±0.09)**、上位3人で **0.48±0.10(0.40±0.12)**。
- 核心の主張: **「these social signatures tend to persist over time, despite considerable turnover in the identity of alters in the ego network」**(=**分布の形は保存され、中身だけ入れ替わる**)。
出典: https://www.pnas.org/doi/10.1073/pnas.1308540110 / DOI: 10.1073/pnas.1308540110

**Wellman & Wong ら (1997) "A decade of network change: Turnover, persistence and stability in personal communities" *Social Networks*.** ✔(検索要約経由)
- **10年間で親密な紐帯のうち残存したのは 27% のみ**。ただし **n=33(トロント在住者)** と極小サンプル。持続する紐帯は「社会的支援を提供した/電話接触が頻繁/親族」。10年の間に結婚した回答者ではネットワークがほぼ完全に入れ替わった。
出典: https://www.sciencedirect.com/science/article/abs/pii/S0378873396002894

**注意**: Saramäki の 24名は**人生の移行期のコホート**であり入替率は上振れしているはず。Wellman は n=33。**「年間何%」という単一の代表値を出せる強い出典は今回見つからなかった=空欄(未確認)。**
【推測】上記2件から当プロジェクトの初期値を置くなら: 全ネットワーク年率入替 **40-60%**、上位5層(support clique)年率入替 **10-20%**。これは推測であり、感度試験対象。

### (c) エージェント社会シムでの辺更新規則の先行例

- **OASIS**: フォロー/アンフォロー/ミュートを**エージェントの行動として**持つ(21行動中に `follow, unfollow, mute, unmute`)。初期ネットワーク生成は **「0.2 probability of following core users, ensuring diversity」**。✔
- **AgentSociety** (arXiv 2502.08691): 1万体超のエージェントが500万インタラクション。「感情・欲求・動機・認知能力」を持つ設計で、移動・雇用・消費・社会的相互作用を実行。✔(検索要約経由。needs の具体的な項目名(hunger/safety等)は**空欄(未確認)**)
  出典: https://arxiv.org/abs/2502.08691
- **辺の追加削除をエンジン規則にした具体的アルゴリズム(閾値・確率式)を明記した先行例は今回特定できず=空欄(未確認)。**

**推奨(行8)**:
- エンジン: 層別スロット `[5, 15, 50, 150]` を**容量制約**として実装。新しい辺を上位層に入れるには既存メンバーを押し出す(=Saramäki の「分布の形が保存され中身が入れ替わる」を機構として再現)。これが**expedientではなくmechanism**として書ける唯一の部分。
- LLM: 「誰との関係を深めたいか」の**候補選択のみ**(押し出し先の決定はエンジン)。呼数: 40万体 × 0.1回/日 = 4万呼(予算の1.0%)。
- 上限値150 と層の比率3 は **expedient**。感度試験は上限50/150/500。
- 較正ターゲット: 「social signature の形状(上位alterへの通信集中度)が入替にかかわらず不変」を holdout 側の検証量に使う。

---

## 問い4: 行9 SNS — 推薦の計算量と現実の拡散統計

### (a) OASIS(先行実装)の推薦アルゴリズムと計算量

**OASIS: Open Agent Social Interaction Simulations with One Million Agents** (arXiv 2411.11581)。✔(WebFetch要約経由)

- **X/Twitter モード**: **「TwHIN-BERT, which models user interests based on profiles and recent activities by vectors' similarity」**。ネットワーク外投稿については **recency(新しい投稿を優先)と投稿者のフォロワー数**を考慮。
- **Reddit モード**: プラットフォーム公開のhotスコアをそのまま実装: **`h = log₁₀(max(|u−d|,1)) + sign(u−d)·(t−t₀)/45000`**(u=upvote, d=downvote, t=時刻)。上位k件を選ぶ。
- **行動空間 21種**: sign up, refresh, trend, search posts, search users, create post, repost, follow, unfollow, mute, like, unlike, dislike, undo dislike, unmute, create comment, like comment, unlike comment, dislike comment, undo dislike comment, do nothing。
- **計算コスト(Reddit実験、Table 2)**: 100体=0.33分/step、1,000体=0.83分/step、**10,000体=15分/step(A100×4)**。
- **100万体実験**: **196のコアエージェント + 100万の一般エージェント**、**60ステップを A100×24 で1週間以内**。総LLM呼数は非公開。
- 拡散再現の精度: Twitter15/16 から **198の実事例**(1事例あたり100-700ユーザー)で評価、**normalized RMSE 約30%**。
出典: https://arxiv.org/abs/2411.11581 / https://github.com/camel-ai/oasis

→ **含意(重要)**: OASISの10,000体で15分/step という数字は、**当プロジェクトの40万体には40倍のスケールがある**。OASISの推薦はスコア全再計算に近い実装であり、**そのままでは移植不可**。「O(feed_size)増分限定」という当方の決定は、OASISに対する明確な改善方向であって、妥協ではない。

### (b) 現実SNSの拡散統計(原文抽出済み)

**Goel, Anderson, Hofman & Watts (2016) "The Structural Virality of Online Diffusion" *Management Science* 62(1): 180-196.** ✔✔ (PDFから原文抽出・逐語)

- データ: **「we observe roughly 622 million unique pieces of content; however, because individual pieces of content can be posted by multiple users, we observe approximately 1.2 billion "adoptions"」**、期間は **2011年7月-2012年6月の12か月**。
- カスケードの大きさ: **「the vast majority of cascades—over 99%—are tiny and terminate within a single generation (Goel et al. 2012)」**
- 大規模カスケードの希少性: **「we restrict attention to the 0.025% of diffusion trees containing at least 100 nodes (Figure 2), a requirement that leaves us with roughly 1 out of every 4,000 cascades, and thus reduces the number of cascades we study in detail from approximately 1 billion to 219,855.」**
- 構造的バイラリティは大きさによらず低い: **「structural virality is typically low, and remains so independent of size, suggesting that popularity is largely driven by the size of the largest broadcast.」** ニュースでは **「For cascades of size 100, for example, median structural virality is approximately 3, whereas for the largest observed news cascades, comprising 3,000 reposts, median structural virality is still less than 8」**。請願(petitions)の中央値は7-8。
- サイズ分布はヘビーテール。感染力 ζ を**べき分布**から引くと経験的なヘビーテール分布が再現できる、と報告。
出典: https://pubsonline.informs.org/doi/10.1287/mnsc.2015.2158 (DOI: 10.1287/mnsc.2015.2158) — **注: informs.org は WebFetch で 403。本文は https://www.cis.upenn.edu/~mkearns/teaching/NetworkedLife/GoelEtAl.pdf および https://5harad.com/papers/twiral.pdf で読める**

**Vosoughi, Roy & Aral (2018) "The spread of true and false news online" *Science* 359(6380): 1146-1151.** ✔(検索要約経由)
- 2006-2017のTwitter、**約126,000のストーリー、約300万人、450万回超のツイート**。
- **「The top 1% of false news cascades diffused to between 1000 and 100,000 people, whereas the truth rarely diffused to more than 1000 people.」**
- 虚偽は真実より遠く・速く・深く・広く拡散。政治的虚偽で効果が最も顕著。
出典: https://pubmed.ncbi.nlm.nih.gov/29590045/ / DOI: 10.1126/science.aap9559

### (c) O(feed_size)増分限定で再現できる範囲

**再現できる(第1陣)**:
- サイズ分布のヘビーテール — 99%が単世代で終わるので、**カスケードの大半は「1回の配信でフォロワーに届く」だけ**。増分更新で十分。
- 構造的バイラリティが低いまま(中央値3程度) — 深い多世代分岐を明示的に追う必要がない。
- ブロードキャスト支配 — フォロワー数の重い裾を初期ネットワーク生成で入れれば、「最大配信の大きさ」が人気を決めるという主要所見が出る。
- Reddit型 hot score(上式)は **O(1)/投稿** で更新でき、feed生成は上位k抽出のみ。

**再現が難しい(第2陣以降 or 諦める)**:
- 上位1%のカスケード(1,000-100,000人規模)は **4,000本に1本**の稀事象。40万体スケールでも**統計的に十分な本数を得るには長いシミュ日数が必要**。【推測】日次投稿数 20万件なら100ノード以上のカスケードは日50本程度=1シミュ日で50サンプル。分布の裾の較正には数十シミュ日が要る。
- 真偽による拡散差(Vosoughi) — 「新規性」「感情反応」の媒介変数が要るので第2陣。

**呼数(重要)**: SNSで**閲覧のたびにLLMを呼ぶと即座に破綻**。40万体 × 10投稿閲覧 = 400万呼で予算全消費。
→ **推奨: 閲覧・推薦・スコア更新は完全エンジン。「反応するか否か」もエンジンの確率ゲート(関心類似度+感情スコアの閾値)。LLMは「投稿本文の生成」と「ゲートを通ったコメントの生成」のみ。** 目安 40万体 × 0.5回/日 = 20万呼(予算の5%)。

---

## 問い5: 行15 記憶 — 減衰・retrievalの先行例と既決定(U1ハイブリッド)との整合点

### 先行例の定数(WebFetchで確認)

**Generative Agents (Park et al., UIST 2023 / arXiv 2304.03442)** ✔(WebFetch要約経由・要一次確認)
- **recency**: **「we treat recency as an exponential decay function over the number of sandbox game hours since the memory was last retrieved. Our decay factor is 0.995」**
- **importance**: 1-10の poignancy 尺度。プロンプトは **「On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance)...」**
- **relevance**: メモリ本文の埋め込みとクエリ埋め込みの**コサイン類似度**。
- **合成の重み**: **「In our implementation, all α alphas are set to 1」**(recency/importance/relevance を等重み)
- **反省(reflection)のトリガ**: **「we generate reflections when the sum of the importance scores for the latest events perceived by the agents exceeds a threshold (150 in our implementation). In practice, our agents reflected roughly two or three times a day.」**
出典: https://arxiv.org/abs/2304.03442

**ACT-R 型減衰** ✔(検索要約経由)
- 基底活性 **B(i) = ln(Σ t_k^(−d))**、t_k は k 回目の想起からの経過時間、**d の既定値は 0.5**(適用範囲全体でACT-Rコミュニティの既定値として定着。典型域 0.3-0.7)。理論的裏付けは Anderson & Schooler (1991) の**練習と忘却のべき法則**。
出典: https://www.ai.rug.nl/~niels/publications/taatgenLebiereAnderson.pdf

**人間の忘却曲線の代表値(Ebbinghaus の保持率など)**: 今回**一次確認できず=空欄(未確認)**。ACT-R のべき法則(Anderson & Schooler 1991)が同じ現象の定量版なので、これで代替可能。

### 既決定(U1ハイブリッド)との整合点 — 簡潔に

1. **減衰と retrieval は完全にエンジン側で成立する**。GAの 0.995(ゲーム内時間の1時間ごと)も ACT-R の d=0.5 も、**LLM呼び出しを1回も必要としない閉じた式**。U1ハイブリッドの「エンジン=減衰・retrieval / LLM=反省」の線引きは先行実装と完全一致。
2. **GAの3成分(recency, importance, relevance)のうち、importance だけがLLMを要する**。40万体で全記憶に importance を付けるとここが第2の費目になる。**推奨: importance はエンジン側のヒューリスティック(イベント種別 × 関与人数 × 金額/被害の大きさ)を第1陣、LLM採点は第2陣のablation対照**。expedient宣言つき。
3. **【最重要・呼数】反省が予算を食い潰す**。GAの実測「1日2-3回」を40万体に素直に掛けると **80万-120万呼/シミュ日 = 400万呼予算の20-30%**。【試算】
   → **対策**: 重要度合計の閾値を 150 から大幅に引き上げる、または「反省するエージェントを日次でサンプリング(例: 5%)」する。**閾値そのものを予算制御パラメータとして宣言し、感度試験で「反省頻度を1/10にしても社会現象が変わらない」ことを示す**のが第1陣の完了条件。
4. **減衰係数の単位に注意**。GAの 0.995 は「**最後に想起されてから**のゲーム内時間(時間単位)」。1日=24時間で 0.995^24 ≈ 0.887、1週間で 0.43、1か月で 0.026。当プロジェクトのtick粒度が時間でないなら**係数の再導出が必要**(この換算は【推測】=私の計算)。

---

## 問い6: 行16 未定義行動の受理

### 先行例

**Voyager (Wang et al., arXiv 2305.16291)** ✔(検索要約経由)
- 3要素: **(1) 探索を最大化する自動カリキュラム、(2) 複雑な行動を保存・検索する ever-growing skill library of executable code、(3) 環境フィードバック・実行エラー・自己検証を取り込む反復プロンプト機構**。
- スキルは **temporally extended, interpretable, and compositional**。GPT-4 へのブラックボックス問い合わせのみでファインチューニング不要。
- 成果: **ユニークアイテム3.3倍、移動距離2.3倍、テックツリー到達最大15.3倍速**。新しい世界でスキルライブラリを再利用可。
出典: https://arxiv.org/abs/2305.16291 / https://voyager.minedojo.org/

→ **当プロジェクトへの含意**: Voyagerの核心は「**新規行動を自然言語で受理するのではなく、実行可能コードとして受理し、環境の実行結果で検証する**」点。**自己検証(self-verification)が受理判定を担っている**。当方の「エンジン規則で受理判定」はこれと同じ思想で、より軽い(コード実行ではなくスキーマ検証)。

**PDDL/STRIPS の前提条件・効果スキーマ** ✔(検索要約経由)
- STRIPS/PDDL は行動を **「実行前に必要な条件」と「実行後に生じる効果」** で表現。PDDLのaction定義は **action name / parameters / precondition / effect** の4要素。precondition は述語と論理演算子(and, or, not, exists)からなる一階述語論理文。
- 近年の LLM 応用: Contract2Tool(ツールを状態遷移とみなし前提条件と効果を推論)、PDDLCoder(PDDL生成を反復的に作成・精緻化・検証)、PDDL-INSTRUCT(前提条件-効果構造を論理的CoTで教える)、NL-pddlgym(23ドメイン711問題+実行可能環境で**plan applicability を直接評価**)。
出典: https://arxiv.org/html/2606.07904 / https://arxiv.org/html/2608.16637 / https://arxiv.org/pdf/2509.13351

**AI Town / "emergent action" 系**: 今回**調査できず=空欄(未確認)**。

### 推奨: 3層の受理パイプライン(すべてエンジン規則)

LLMが出力した未定義行動テキストを、以下の順に**エンジンだけで**処理する。LLM追加呼び出しはゼロ。

| 層 | 判定 | エンジン規則 | 結果 |
|---|---|---|---|
| **L1: 既存動詞へのマッピング** | 提案が既存WorldProcess行の言い換えか | 動詞の埋め込み類似度 ≥ θ かつ引数の型が既存スキーマに適合 | 既存行として実行。**大半(【推測】9割超)はここで吸収されるはず** |
| **L2: パラメータ拡張** | 既存動詞だが引数が新規(新しい対象物・新しい場所) | 対象が台帳(POI 2,337 / 組織1.1万 / 品目)に存在するか、または新規オブジェクト生成が保存則に反しないか | 実行 + 引数を台帳に追記 |
| **L3: 新動詞の検疫** | 既存に写像できない新しい動詞 | ① **前提条件テンプレの充足**: 提案行動が要求する状態述語(位置・所持・関係・時刻・許可)がすべて現在状態で真か。② **効果のスキーマ検証**: 効果が(a)既存の状態変数の型に収まるか、(b)**保存量(通貨・在庫・人数)を勝手に生成/消滅させていないか**——生成/消滅を伴うなら**faucet/sink として明示登録できるか**。③ 性能予算: 新規ループを増やさないか。 | 3条件を通れば **新しいWorldProcess行として承認待ちキューへ**。通らなければ**却下ログ**(却下も記録する=カバー率の分母) |

**設計上の要点**:
- **却下ログを必ず残す**。「未定義行動の受理率」がパターン台帳ゲートの計測量になる。受理率が高すぎれば世界が壊れ、低すぎれば創発が死ぬ。
- **L3の②が保存則運用②と直結**。「効果が保存量を動かすなら faucet/sink 登録を強制」というルールは、行16を**保存則の防波堤**として機能させる。これは当プロジェクト固有の強みで、先行研究に対応物が見当たらない(=空欄(未確認)、独自性の主張候補)。
- **等級**: L1/L2 は C(先行実装の慣行)、L3 は E(設計判断)。L3 の閾値はすべて expedient。
- **陣**: L1・L2 は第1陣(これが無いと行動が全部落ちる)。L3 は第2陣(創発の観察が目的なので、世界が安定してから開ける)。

---

## 問い7: 行2(待ち行列)・行10(健康)・行12(犯罪検知)

### 行2: 施設の収容・待ち行列

**現実値(等級D — すべて業界メディアが出所。公的統計ではない)** ✔(検索要約経由)
- 業態別の**客席回転率の目安**: ファストフード **20回**、レストラン・居酒屋 **2〜3回**、フルコースのレストラン **1回**。
- **客席稼働率の平均は 65〜70%**(実際の客数 ÷ テーブル着席可能人数)。
- 平日/休日、ランチ/ディナーを分けて考えるのが実務の標準。
出典: https://insyoku-mikata.vector.co.jp/posts/168/ / https://canaeru.usen.com/diy/opening/p959/

**渋谷区の店舗別席数の実データ**: 今回**見つからず=空欄(未確認)**。経済センサスには席数の項目が無いため、【推測】従業者数 → 席数の換算式を立てるしかない(例: 飲食店の席数 ≒ 従業者数 × 6-10)。これは **expedient・要感度試験**。

**推奨実装**: エンジンの M/M/c 近似。容量 c(席数)、サービス時間 = 業態別の平均滞在時間(回転率の逆数 × 営業時間)、待ち行列長が閾値を超えたらエージェントは**離脱**(=行1の目的地再選択へ戻す)。稼働率のターゲットは 65-70%。**LLM呼び出しゼロ**。

### 行10: 健康 — 最小形

**先行例**: AgentSociety が「感情・欲求・動機・認知能力」を持つとするが、**健康状態機械の具体的な状態リストを持つ先行例は今回特定できず=空欄(未確認)**。

**推奨(最小形・すべて【推測】=設計判断、等級E)**:
- 連続量2本: `fatigue ∈ [0,1]`(活動で増、睡眠で減)、`nutrition ∈ [0,1]`(時間で減、飲食で増)。
- 離散状態5つ: `{健常, 軽度不調, 就業不能, 入院, 死亡}`。遷移はエンジンの確率(年齢別・fatigue/nutrition依存)。
- **保存則との接続**: 医療費は sink、傷病手当は faucet。入院は施設収容(行2)を消費。死亡は人口の sink として**必ず登録**。
- **expedient宣言必須**。第2陣。健康が第1陣の社会現象(移動・消費・SNS)を駆動していないことを感度試験で示す。

### 行12: 犯罪の検知・立件 — 公的統計で二段確率が組める(等級A)

**検挙側(警察庁『令和6年の犯罪情勢』令和7年2月・PDF原文抽出)** ✔✔ 逐語:
- 認知件数: **「刑法犯認知件数の総数については、平成15 年から令和３年まで一貫して減少してきたところ、令和６年は73 万7,679 件と、戦後最少となった令和３年から３年連続で前年を上回った（前年比4.9％増加）」**
- 人口比: **「人口千人当たりの刑法犯認知件数については5.9 件」**
- 罪種内訳: **「窃盗犯が50 万1,507 件（前年比3.7％増加）…風俗犯が１万8,465 件（前年比56.8％増加）、凶悪犯が7,034 件（前年比22.3％増加）、知能犯が６万1,986 件（前年比23.9％増加）」**
- **検挙**: **「刑法犯の検挙件数については、検挙件数は28 万7,273 件、検挙人員は19 万1,826 人と、共に前年（26 万9,550 件、18 万3,269 人）を上回り（それぞれ前年比6.6％、4.7％増加）、刑法犯の検挙率は38.9％と増加した（前年比0.6 ポイント増加）」**
- **罪種別検挙率**: **「重要犯罪の検挙率は86.5％、重要窃盗犯の検挙率は55.7％と、いずれも前年を上回った（それぞれ前年比4.7 ポイント、4.3 ポイント増加）」**
- 街頭犯罪 **25万5,247件**(前年比+4.6%)、侵入犯罪 **5万3,568件**(同 -3.1%)。
- 詐欺: **「詐欺の認知件数について、令和６年は前年比で24.6％増加して５万7,324 件」**、財産犯被害額 **約4,021億円**(うち詐欺 約3,075億円)、詐欺の犯行動機は**「生活困窮」が39.9%で最大**。
出典: https://www.npa.go.jp/publications/statistics/kikakubunseki/r6_jyosei.pdf

参考(令和5年・法務省『令和6年版 犯罪白書』): 刑法犯認知件数 **70万3,351件**、発生率 **565.6**。窃盗の検挙率 **32.5%**、刑法犯検挙率 **38.3%**(後2者は検索要約経由 ✔、白書本文ページからは表が画像/Excelのため**逐語確認できず**)。
出典: https://hakusyo1.moj.go.jp/jp/71/nfm/n71_2_1_1_1_1.html / https://hakusyo1.moj.go.jp/jp/71/nfm/n71_2_1_1_2_3.html

**暗数側(法務省『犯罪被害実態(暗数)調査』・4年ごと)** ✔(検索要約・警察庁白書コラム経由)
- 被害申告率 = 被害に遭った世帯/個人のうち捜査機関に届け出た比率。
- **「バイク盗、自動車盗及び車上盗では、過半数が被害申告をしていますが、自動車損壊や不法侵入未遂では、申告率は３割を下回る」**
- **「平成20年調査の被害申告率を見ると、いずれも申告率が50％以下であり、被害の過半数は警察等に認知されていない「暗数」である」**
- **「ほとんどの被害態様において、『届出なし』の回答が約２割から７割に及んでおり」**
- **罪種別の具体的パーセント値は本文でなく図にあり、今回は 空欄(未確認)**。第6回調査は法務総合研究所研究部報告67(令和7年3月刊)。
出典: https://www.moj.go.jp/housouken/houso_houso34.html / https://www.npa.go.jp/hanzaihigai/whitepaper/w-2013/html/zenbun/part2/s2_4_2c06.html

**推奨実装(行12)**: **二段の独立確率をエンジンで持つ**。
```
P(立件 | 犯行) = P(申告 or 現認 | 犯行) × P(検挙 | 認知)
```
- 第2項は罪種別に**公的数値を直接代入**: 重要犯罪 0.865 / 重要窃盗犯 0.557 / 刑法犯全体 0.389 / 窃盗 0.325。**mechanism・等級A**。
- 第1項は暗数調査から罪種別に 0.2-0.5 のレンジ。**具体値は現状 expedient・等級B**(第6回調査報告67の図を入手できれば等級Aに昇格)。
- **較正の副産物**: 「認知件数 = 犯行件数 × 申告率」が成り立つので、**シミュ内の犯行総数を現実の認知件数73万7,679件(全国)から渋谷区分に按分して逆算**でき、行11(LLMの犯罪実行選択)の**出力を較正する外部アンカー**になる。これは強い。
- 人口比 5.9件/千人 も、40万体スケールでの年間認知件数期待値(≈2,360件/年)を直接与える。

---

## 問い8: 16行の推奨(1行ずつ)

呼数の分母 = **400万呼/シミュ日**(40万体で1体10呼/日)。

| # | 行 | 決定案(エンジン / LLM の線) | 等級 | expedient宣言 | 陣 | 呼数試算 |
|---|---|---|---|---|---|---|
| 1 | 移動・経路 | エンジン=経路探索+混雑コスト / LLM=**目的地の選好のみ**(行き先候補からの選択) | B | 混雑コスト係数 | 第1陣 | 40万×1/日=40万(10%) |
| 2 | 施設の収容・待ち行列 | エンジン全部(M/M/c近似・容量c・離脱閾値) / LLMなし | **D** | 席数換算式・回転率・離脱閾値(全部) | 第1陣 | 0 |
| 3 | 時計・日次遷移 | エンジン全部 / LLMなし | E | tick粒度 | 第1陣 | 0 |
| 4 | 所持金・売買の成立 | エンジン強制(取引レベルの保存はハード制約) / LLMなし | **A** | なし(mechanism) | 第1陣 | 0 |
| 5 | **価格形成** | **A案**: エンジン=内生フロア(原価×k)+クリアリング+逸脱比例コスト(sink登録)+Calvo型改定確率 / LLM=**相対倍率スカラー r** | B | k, β, 改定確率(現実の月次改定頻度~20%で較正) | 第1陣 | 2,337店×1/日=**2.3千(0.06%)** |
| 6 | 雇用・賃金 | 行5と同型。ただしフロア=**東京都最低賃金1,226円/時(外生・mechanism)**。下方硬直は**弱いペナルティ**(硬い禁止にしない) | **A**(フロア) / B(硬直) | 硬直ペナルティ係数・α_w | 第1陣 | 1.1万組織×1/月=**367/日(0.01%)** |
| 7 | 会話 | エンジン=配送・到達判定のみ / LLM=発話生成 | E | 会話成立の距離・確率 | 第1陣 | 発話数に比例(要別途上限) |
| 8 | 社会関係グラフ | エンジン=層別スロット[5,15,50,150]の**容量制約と押し出し** / LLM=関係を深める候補の選択のみ | **C**(Dunbar批判あり) | 上限150・比率3・入替率(全部) | 第1陣(上限)/第2陣(層別) | 40万×0.1/日=4万(1%) |
| 9 | SNSフィード・拡散 | エンジン=推薦(hot score型 O(1)更新 + 関心類似度)・**反応するか否かの確率ゲート** / LLM=投稿本文とコメントの生成のみ | B | 反応ゲートの閾値・feed_size | 第1陣 | 40万×0.5/日=20万(5%) |
| 10 | 健康 | エンジン=fatigue/nutritionの連続量2本 + 5状態機械 / LLMなし | **E** | 全パラメータ | 第2陣 | 0 |
| 11 | 犯罪の実行選択 | **LLM**(創発の観察対象) / エンジン=機会の提示ゲート(場所・時刻・対象の可用性) | E | 機会ゲートの閾値 | 第2陣 | ゲート後のみ 40万×0.001=400(0.01%) |
| 12 | 犯罪の検知・立件 | エンジン=**二段確率** P(申告)×P(検挙)。P(検挙)は公的値を直接代入 | **A**(検挙) / B(申告) | 申告率の罪種別値 | 第2陣 | 0 |
| 13 | 立法(条文生成) | **LLM**(条文生成) / エンジン=可決手続・施行日・条文の機械可読化 | E | 議決規則 | 第2陣 | 極小(制度体のみ) |
| 14 | 違反判定・紛争裁定 | エンジン=判例の検索(埋め込み+条文タグ)・再適用の記録 / LLM=当てはめ判断 | E | 検索の類似度閾値 | 第2陣 | 紛争件数に比例 |
| 15 | 記憶・忘却・想起 | エンジン=減衰(ACT-R d=0.5 or GA 0.995相当)・retrieval・**importanceもエンジンのヒューリスティック** / LLM=反省のみ(**強い頻度ゲート**) | **C** | 減衰係数・importance式・反省閾値 | 第1陣 | **反省を絞らないと80-120万(20-30%)** ← 最大費目 |
| 16 | 未定義行動の受理 | エンジン=L1マッピング/L2パラメータ拡張/L3スキーマ検証(前提条件充足+効果の型+保存量のfaucet/sink登録強制) / LLM=提案のみ | C(L1/L2) / E(L3) | 類似度θ・L3の全条件 | 第1陣(L1/L2) / 第2陣(L3) | 0(追加呼び出しなし) |

**呼数の合計試算(第1陣・反省を絞る前)**: 1(40万) + 5(0.2万) + 6(0.04万) + 8(4万) + 9(20万) + 15(80-120万) ≒ **144-184万呼/シミュ日 = 予算の36-46%**。行7(会話)と行1の再計画が上乗せされる。**行15の反省頻度が唯一の大きな調整弁**。

---

## 問い9: 親の一次確認リスト(最重要5件)

| # | 主張 | URL | 確認すべきこと | 引用文(現状) |
|---|---|---|---|---|
| 1 | **LLM価格エージェントは自律的に超競争価格へ収束する**(行5の設計根拠の核) | https://arxiv.org/abs/2404.00806 (HTML: /html/2404.00806v5) | ①要旨の逐語、②**価格上限「2.34⋅p^M, 2.34 ~ Unif([1.5,2.5])」と限界費用 c_i=1 が本当に本文にあるか**(WebFetch要約経由のため未確定)、③P1/P2の p<0.00001、④出版状況(abs頁に EC 2026 accepted の表示あり) | 「In oligopoly settings, LLM-based pricing agents quickly and autonomously reach supracompetitive prices and profits.」 |
| 2 | **EconAgentはLLMに価格を出させず、価格・賃金はエンジン規則**(行5・行6の中間案の正当化) | https://aclanthology.org/2024.acl-long.829/ / https://arxiv.org/abs/2310.10436 | ①**α_P=0.10, α_w=0.05, φ̄=(D−G)/max(D,G)** の式と数値、②LLM出力が work/consumption の[0,1]・刻み0.02 であること、③N=100体・240か月・約$30/2時間 | 「w_i ← w_i(1+φ_i), φ_i ~ sign(φ̄)U(0, α_w|φ̄|)」「a value between 0 and 1 with intervals of 0.02」 |
| 3 | **Dunbar 150に統計的支持がない**(行8の等級をA/B→Cに落とす根拠) | https://royalsocietypublishing.org/doi/abs/10.1098/rsbl.2021.0158 / PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC8103230/ | 「69–109」「16–42」という2組の推定値が要旨にあるか。DOI: 10.1098/rsbl.2021.0158 | 「Bayesian and generalized least-squares phylogenetic methods generated approximations of average group sizes between 69–109 and 16–42, respectively」 |
| 4 | **反省(reflection)が予算の20-30%を食う**(行15の最大リスク・**私の試算**) | https://arxiv.org/abs/2304.03442 | ①「decay factor is 0.995」「threshold (150)」「roughly two or three times a day」「all α alphas are set to 1」が本文にあるか、②**40万体×2.5回/日=100万呼=25% という私の算術の再計算**、③0.995の時間単位が「ゲーム内時間(hours) since last retrieved」であることの確認(換算式に効く) | 「we generate reflections when the sum of the importance scores for the latest events perceived by the agents exceeds a threshold (150 in our implementation). In practice, our agents reflected roughly two or three times a day.」 |
| 5 | **犯罪検知の二段確率に使う公的数値**(行12を等級Aにする根拠) | https://www.npa.go.jp/publications/statistics/kikakubunseki/r6_jyosei.pdf | 検挙率38.9% / 重要犯罪86.5% / 重要窃盗犯55.7% / 認知件数73万7,679件 / 人口千人当たり5.9件。**この5値は私がPDFを原文抽出して目視確認済み(✔✔)だが、資料が「確定値」注記つきである点(脚注3)を親が確認すること**。加えて暗数側の**罪種別申告率の具体値は未取得**——法務総合研究所研究部報告67(第6回暗数調査)の入手可否を判断されたい | 「刑法犯の検挙率は38.9％と増加した（前年比0.6 ポイント増加）」「重要犯罪の検挙率は86.5％、重要窃盗犯の検挙率は55.7％」 |

**補助的に確認が要る項目**: 東京都最低賃金の**2026年度改定額(1,280円説)**は非公式サイト出所のため未確認。厚労省/東京労働局の公式発表で置き換えること。

---

## 参照一覧

| 分類 | 著者・年・出典 | URL | 確認状況 |
|---|---|---|---|
| 行5 | Fish, Gonczarowski & Shorrer (2024) "Algorithmic Collusion by Large Language Models", arXiv:2404.00806 | https://arxiv.org/abs/2404.00806 | ✔ 要旨は逐語確認。上限2.34・c=1・P1/P2の数値はWebFetch要約経由=**要一次確認** |
| 行5 | Calvano, Calzolari, Denicolò & Pastorello (2020) *AER* 110(10):3267-97 | https://www.aeaweb.org/articles?id=10.1257/aer.20190623 | ✔ 検索要約経由 |
| 行5 | Chen et al. (2023) "The emergence of economic rationality of GPT", *PNAS* | https://www.pnas.org/doi/10.1073/pnas.2316205120 / https://arxiv.org/abs/2305.12763 | ✔ 検索要約経由(GARP件数・CCEI値) |
| 行5/6 | Li, Gao, Li, Li & Liao (2024) "EconAgent", ACL 2024 Long 829 / arXiv:2310.10436 | https://aclanthology.org/2024.acl-long.829/ | ✔ WebFetch要約経由=**要一次確認** |
| 行5 | Zhao et al. (2024) "CompeteAI", ICML 2024 Oral / arXiv:2310.17512 | https://arxiv.org/abs/2310.17512 | ✔ 検索要約のみ(定性的所見: 社会的学習・累積優位) |
| 行5 | Roblox Creator Hub "Marketplace fees and commissions"(累進レベニューシェア・30%手数料) | https://create.roblox.com/docs/marketplace/marketplace-fees-and-commissions | ✔ 検索要約経由。**dynamic price floor 導入日(2024-02-22)とフロア値はFandom wiki出所=要一次確認** |
| 行5 | 日本の価格粘着性(月次改定頻度 約20%)、東大CARF WP F570 / *Japanese Economic Review* | https://www.carf.e.u-tokyo.ac.jp/wp/wp-content/uploads/2023/09/F570.pdf / https://link.springer.com/article/10.1007/s42973-024-00161-w | ✔ 検索要約経由 |
| 行6 | 東京都最低賃金 1,226円(令和7年10月3日発効) | https://www.city.taito.lg.jp/bunka_kanko/koyo_shugyo/jigyousya/2025tokyo_saichin.html | ✔ WebFetchで確認(自治体公式)。**2026年度分は空欄(未確認)** |
| 行6 | Kuroda & Yamamoto, BOJ/IMES "Are Japanese Nominal Wages Downwardly Rigid?" | https://www.imes.boj.or.jp/research/papers/english/03-E-03.pdf / https://www.imes.boj.or.jp/research/papers/english/me25-2-2.pdf | ✔ 検索要約経由 |
| 行6 | 連合2025年春闘最終集計 5.25%(ベア3.7%・中小4.65%) | https://www.jil.go.jp/kokunai/blt/backnumber/2025/07/shuzai_01.html | ✔ 検索要約経由 |
| 行8 | Zhou, Sornette, Hill & Dunbar (2005) *Proc R Soc B* 272(1561):439-444, DOI:10.1098/rspb.2004.2970 | https://royalsocietypublishing.org/doi/10.1098/rspb.2004.2970 | ✔ 検索要約経由 |
| 行8 | Dunbar (2020) *Proc R Soc A* 476, 層の機能名 | https://pubmed.ncbi.nlm.nih.gov/32922160/ | ✔ 検索要約経由。**層の機能名の記述は二次資料混入=要一次確認** |
| 行8 | Lindenfors, Wartel & Lind (2021) *Biol Lett* 17:20210158, DOI:10.1098/rsbl.2021.0158 | https://royalsocietypublishing.org/doi/abs/10.1098/rsbl.2021.0158 | ✔ 検索要約経由 |
| 行8 | **Saramäki et al. (2014) *PNAS* 111(3):942-947, DOI:10.1073/pnas.1308540110** | https://www.pnas.org/doi/10.1073/pnas.1308540110 | **✔✔ PDF原文抽出で逐語確認**(Jaccard 0.22/0.27, top20 0.36/0.44, top5 0.39, n=24, 18か月) |
| 行8 | Wellman & Wong (1997) "A decade of network change", *Social Networks* | https://www.sciencedirect.com/science/article/abs/pii/S0378873396002894 | ✔ 検索要約経由(27%persist, n=33) |
| 行8/9 | Yang, Zhang et al. (2024) "OASIS", arXiv:2411.11581 | https://arxiv.org/abs/2411.11581 | ✔ WebFetch要約経由(hot score式・行動21種・15分/step@10k・1M体×60step@A100×24) =**要一次確認** |
| 行8/10 | Piao et al. (2025) "AgentSociety", arXiv:2502.08691 | https://arxiv.org/abs/2502.08691 | ✔ 検索要約のみ。**needsの具体項目は空欄(未確認)** |
| 行9 | **Goel, Anderson, Hofman & Watts (2016) *Management Science* 62(1):180-196, DOI:10.1287/mnsc.2015.2158** | https://www.cis.upenn.edu/~mkearns/teaching/NetworkedLife/GoelEtAl.pdf(informs本体は403) | **✔✔ PDF原文抽出で逐語確認**(>99%単世代・0.025%が100ノード以上・1.2B adoptions・219,855本) |
| 行9 | Vosoughi, Roy & Aral (2018) *Science* 359(6380):1146-1151, DOI:10.1126/science.aap9559 | https://pubmed.ncbi.nlm.nih.gov/29590045/ | ✔ 検索要約経由(上位1%が1,000-100,000人) |
| 行15 | Park et al. (2023) "Generative Agents", arXiv:2304.03442 (UIST'23) | https://arxiv.org/abs/2304.03442 | ✔ WebFetch要約経由(0.995・importance 1-10・α=1・閾値150・1日2-3回)=**要一次確認** |
| 行15 | ACT-R base-level activation, d=0.5 既定 / Anderson & Schooler (1991) | https://www.ai.rug.nl/~niels/publications/taatgenLebiereAnderson.pdf | ✔ 検索要約経由 |
| 行15 | Ebbinghaus 忘却曲線の代表値 | — | **空欄(未確認)** |
| 行16 | Wang et al. (2023) "Voyager", arXiv:2305.16291 | https://arxiv.org/abs/2305.16291 | ✔ 検索要約経由 |
| 行16 | PDDL/STRIPS 前提条件・効果スキーマ + LLM応用(Contract2Tool / PDDLCoder / PDDL-INSTRUCT / NL-pddlgym) | https://arxiv.org/html/2606.07904 / https://arxiv.org/html/2608.16637 / https://arxiv.org/pdf/2509.13351 | ✔ 検索要約経由 |
| 行16 | AI Town / "emergent action" 研究 | — | **空欄(未確認・今回調査せず)** |
| 行2 | 飲食店の回転率・客席稼働率(業界メディア) | https://insyoku-mikata.vector.co.jp/posts/168/ / https://canaeru.usen.com/diy/opening/p959/ | ✔ 検索要約経由。**等級D。渋谷の実店舗席数は空欄(未確認)** |
| 行12 | **警察庁『令和6年の犯罪情勢』(令和7年2月)** | https://www.npa.go.jp/publications/statistics/kikakubunseki/r6_jyosei.pdf | **✔✔ PDF原文抽出で逐語確認**(検挙率38.9/86.5/55.7%・認知73万7,679件・5.9件/千人・詐欺5万7,324件) |
| 行12 | 法務省『令和6年版 犯罪白書』(令和5年分) | https://hakusyo1.moj.go.jp/jp/71/nfm/n71_2_1_1_1_1.html | ✔ 認知件数70万3,351件・発生率565.6はWebFetchで確認。**検挙率38.3%・窃盗32.5%は検索要約経由で表が画像のため未逐語=要一次確認** |
| 行12 | 法務省『犯罪被害実態(暗数)調査』/ 警察庁『犯罪被害者白書』コラム | https://www.moj.go.jp/housouken/houso_houso34.html / https://www.npa.go.jp/hanzaihigai/whitepaper/w-2013/html/zenbun/part2/s2_4_2c06.html | ✔ 定性記述のみ確認。**罪種別申告率の具体値は図中のため 空欄(未確認)** |

---

## 付記: 今回できなかったこと(空欄の明示)

1. LLM価格エージェントの**桁外れ出力の頻度**を直接報告した研究 — 見つからず。
2. **AI Town** および "emergent action" 系の調査 — 未着手。
3. **Ebbinghaus 忘却曲線の代表値** — 未確認(ACT-R のべき法則で代替可能と判断)。
4. **渋谷区の店舗別席数** の実データ — 見つからず。回転率・稼働率は業界記事(等級D)のみ。
5. **暗数調査の罪種別被害申告率の数値** — 本文になく図のみ。第6回調査(研究部報告67)の本体未参照。
6. **社会関係グラフの辺更新規則を式で明記した先行実装** — 特定できず。
7. 東京都最低賃金の**2026年度改定額** — 公式出所を確認できず。
8. 行13(立法)・行14(裁定)は先行研究を調べる時間が取れず、推奨は**設計判断(等級E)のみ**。
