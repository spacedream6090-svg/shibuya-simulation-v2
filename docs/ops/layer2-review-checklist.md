# 層2 独立検収チェックリスト(工程出口・別インスタンスのFableが実施)

> 根拠: 実装計画書 §9.6(b) 層2・§9.5(c)(e)(f)・CLAUDE.md §5(サブの完了報告は信用せず、ディスク実在+pytest で検収)。
> レビュー役は作業役と別のコンテキストで起動し(Agent ツール model:"fable")、**自分でコマンドを実行して**確かめる。作業役の主張・サブの報告は証拠にしない。

## 手順(必ず全部を自分で実行する)

1. **ディスク実在**: 工程の成果物(パッケージ・テスト・CI・設定)が実在するか `git status` / `ls` で確認。未追跡ファイルの一覧を報告に含める。
2. **pytest 再実行**: `.venv/Scripts/python.exe -m pytest -o addopts="-p no:cacheprovider" -p no:cacheprovider` を自分で実行し、passed/failed 件数を写す。作業役の貼った出力と件数が一致するか。
3. **層契約**: `.venv/Scripts/lint-imports.exe` を実行し「Contracts: N kept, 0 broken」を確認。
4. **秘密スキャン**: `git ls-files -z | xargs -0 python tools/scan_secrets.py` と、未追跡の新規ファイルに対する `python tools/scan_secrets.py <files>` の両方が CLEAN。
5. **設計適合**: 工程の内容(実装計画書 §9.1 の該当行)と受入列を読み、成果物が各項目に対応しているかを 1 項目 1 行で判定(対応/不足/逸脱)。設計書の決定項と食い違う実装があれば「逸脱」として列挙。
6. **台帳不変**: `git diff --stat main -- docs/design/` を見て、設計書の変更が **expedient 登録簿への追記のみ**であること(決定項・表・数値の書き換えがないこと)。
7. **expedient 登録簿**: 工程で導入した自前規約(命名・初期値・簡略化)が登録簿(実装計画書 §8 または各設計書の登録簿)に追記されているか。未登録があれば列挙。
8. **data/ 未追加**: `git ls-files data` が空。`git diff --cached --name-only` に data/ が無い。
9. **ブランチ**: 作業が `build/<工程ブランチ>(例 build/c5-c8)` にあり main に触れていない(`git branch --show-current`)。
10. **テストの質(抜き取り)**: テストファイルを 1〜2 本読み、(a) 常に真になる検査(`assert True` 相当・例外を握りつぶす)がないか (b) 受入列の各項目に対応するテストが実在するか。

## 報告形式(固定)

```
判定: 合格 / 不合格
実行したコマンドと結果(1行ずつ): ...
設計適合表: 項目 | 判定 | 根拠(ファイル:行)
逸脱・不足(あれば): ...
expedient 未登録(あれば): ...
```

不合格の場合は「何を直せば合格か」を具体的に書く。合格の場合も、次工程に持ち越す懸念を最大 3 件書く。

> (層2 09-09 注記) pyproject の addopts に `-q -p no:cacheprovider` があるため、コマンド側の `-q` は総括行を消す(`-qq` 相当)。件数は `-o addopts="-p no:cacheprovider"` で取る。
