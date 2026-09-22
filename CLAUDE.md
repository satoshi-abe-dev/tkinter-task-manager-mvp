# tkinter-task-manager-mvp 用ルール

## 開発フロー

- 変更は必ず **feature ブランチ → Pull Request → squash merge**。**main への直接 push はしない**
- CI（`.github/workflows/test.yml`）は PR 上でも走るので、マージ前に結果を確認する
- 可能であれば PR を出す前に `pytest` をローカルで通しておく

## 言語

- コミットメッセージ、PR のタイトル・本文、Issue は英語で書く（2026-09-22 以降）
- コード内コメント・docstring は英語で書く（2026-09-22 以降。以前は日本語だったが全て英訳済み）
- README（`README_ja.md` / `README_en.md`）は日英を必ずミラーして更新する。片方だけの更新はしない
