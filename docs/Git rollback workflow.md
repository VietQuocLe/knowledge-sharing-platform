# Quy trình Git đơn giản: Checkpoint & Rollback khi code với AI

Dùng cho mỗi lần để Copilot/AI chỉnh sửa code trong project.

---

## Bước 1 — Đặt checkpoint TRƯỚC khi để AI code

```bash
git add -A
git commit -m "checkpoint: before <mô tả ngắn task>"
```

> Đây là "cờ" để quay lại nếu cần. Ví dụ: `checkpoint: before resource crud`

---

## Bước 2 — Để AI code như bình thường

Không cần làm gì thêm ở bước này.

---

## Bước 3 — Kiểm tra AI đã đổi những gì

```bash
git status
git diff
```

Đọc kỹ trước khi quyết định giữ hay bỏ. AI đôi khi sửa nhầm chỗ không liên quan.

---

## Bước 4a — Nếu ƯNG Ý: commit lại đúng convention

```bash
git add -A
git commit -m "feat: <mô tả theo convention project>"
```

(Có 2 commit liên tiếp — checkpoint + commit thật — không sao, không cần gộp nếu không rảnh.)

---

## Bước 4b — Nếu KHÔNG ƯNG: rollback về checkpoint

```bash
git reset --hard HEAD~1
```

⚠️ Lệnh này xóa vĩnh viễn toàn bộ thay đổi của AI, không cứu lại được. Chỉ chạy khi chắc chắn.

---

## Ghi nhớ nhanh

| Muốn làm gì | Lệnh |
|---|---|
| Tạo điểm mốc trước khi AI code | `git add -A && git commit -m "checkpoint: ..."` |
| Xem AI đổi gì | `git status` / `git diff` |
| Giữ lại thay đổi | `git add -A && git commit -m "feat: ..."` |
| Bỏ hết thay đổi, quay lại checkpoint | `git reset --hard HEAD~1` |

---

## Sau mỗi Sprint

Khi cả sprint đã test ổn, push lên GitHub như bình thường:

```bash
git push origin main
```