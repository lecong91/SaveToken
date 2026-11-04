# SaveToken (Tiếng Việt)

**Hệ Thống Kiểm Soát Chi Phí & Tiết Kiệm Token Đa Nền Tảng Cho Google Antigravity & AI Coding Assistants**  
*Tối ưu hóa hoàn hảo cho macOS và Windows | 100% Python Standard Library (Không phụ thuộc thư viện ngoài)*

[![CI - Multi-OS Test Suite](https://github.com/lecong91/SaveToken/actions/workflows/ci.yml/badge.svg)](https://github.com/lecong91/SaveToken/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)]()

---

## Giới Thiệu Tổng Quan

**SaveToken** là bản chuyển giao và tối ưu hóa chuẩn công nghiệp từ nghiên cứu khoa học của **Microsoft Research & UC Berkeley** (*TokenEconomizer: Active Cost and Loop Control for Agentic Coding*, arXiv:2610.22732, tháng 10/2026), được thiết kế chuyên biệt để hoạt động mượt mà, chuẩn xác trên **Google Antigravity** (`agy`) trên cả hai hệ điều hành **macOS** và **Windows**.

Bằng cách can thiệp vào các vòng đời lifecycle hooks của Agent, SaveToken giúp giảm từ **40% đến 58%** tổng lượng token tiêu thụ mà không làm suy giảm trí thông minh hay khả năng giải quyết bài toán lập trình của mô hình.

### Các Tính Năng Cốt Lõi

1. **Học Micro-skills Liên Session (Continuous Repository Learning)**:
   - Tự động quan sát các lệnh build/test qua từng phiên làm việc của agent trong repository.
   - Khi một sự thật về môi trường được xác nhận lặp lại (ví dụ lệnh test chuẩn là `uv run pytest` chứ không phải `pytest`), SaveToken sẽ tự động chưng cất và bơm vào ngữ cảnh đầu phiên (`SessionStart`). Agent không còn phải mất 3–8 lượt thử sai mò mẫm mỗi khi mở session mới.
2. **Tự Động Cắt Tỉa Công Cụ Không Dùng (`toolprune`)**:
   - Trong môi trường Antigravity có cài nhiều plugin, MCP server hoặc skill, schema mô tả công cụ có thể chiếm hàng nghìn token trong mỗi lượt gọi prompt.
   - SaveToken tự động thống kê và loại bỏ các công cụ "ngủ quên" khỏi định nghĩa prompt, giúp tiết kiệm từ 1.000 đến 5.000 token trong từng lượt giao tiếp.
3. **Bộ Cắt Vòng Lặp Lỗi Lặp Lại (`loopguard`)**:
   - Tự động nhận diện dấu hiệu bế tắc: Agent sửa code đi sửa lại một vị trí nhưng liên tục gặp lỗi tương tự, hoặc chạy cùng một lệnh thất bại nhiều lần.
   - Can thiệp bằng tin nhắn ngắn (`ephemeralMessage`), hướng dẫn agent dừng lại, phân tích lại log lỗi thay vì đốt thêm token vô ích.
4. **Sổ Cái Token Nhận Biết Cache (`ledger`)**:
   - Tính toán chính xác lượng token được prompt cache (Gemini Cache, Claude Cache), quy đổi ra số USD tiết kiệm được.
5. **Kiến Trúc Thuần Standard Library (Zero-Dependency)**:
   - Chạy trên Python 3.10+ thuần túy, không cần cài đặt thêm bất kỳ gói pip bên ngoài nào khi vận hành.
6. **Hỗ Trợ Toàn Diện macOS & Windows**:
   - Xử lý mượt mà sự khác biệt về đường dẫn, shell (`sh -c` vs `cmd /c`), tiến trình ngầm không giật console, và các biến môi trường người dùng.

---

## Hướng Dẫn Cài Đặt 1-Click

### Dành cho macOS / Linux
Mở Terminal và thực thi:
```bash
git clone https://github.com/lecong91/SaveToken.git
cd SaveToken
./install.sh
```

### Dành cho Windows
Mở PowerShell (với quyền người dùng bình thường):
```powershell
git clone https://github.com/lecong91/SaveToken.git
cd SaveToken
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```
*(Nếu sử dụng Command Prompt `cmd.exe`, bạn chỉ cần chạy `install.bat`)*

### Cài Đặt Bằng Python (Áp dụng mọi hệ điều hành)
```bash
python scripts/install_antigravity.py
```

### Các Bước Sau Khi Cài Đặt:
1. Đảm bảo thư mục binary `~/.tokeneconomizer/bin` (hoặc `%USERPROFILE%\.tokeneconomizer\bin` trên Windows) đã nằm trong biến môi trường `PATH`.
2. Kiểm tra sức khỏe hệ thống:
   ```bash
   te doctor
   ```
3. Khởi động lại Google Antigravity để plugin tự động nạp.

---

## Hướng Dẫn Sử Dụng Lệnh CLI `te`

```bash
# Kiểm tra tình trạng kết nối và plugin Antigravity
te doctor

# Xem trạng thái tiết kiệm token và các hook đang hoạt động
te status --explain

# Danh sách các kiến thức kho lưu trữ (micro-skills) đã học được
te microskills list

# Xem các công cụ đang được đề xuất cắt tỉa để giảm kích thước prompt
te toolprune show

# Xem lịch sử sổ cái token và chi phí
te ledger

# Tổng kết và nén session trò chuyện Antigravity vừa hoàn thành
te fold --session <mã_conversation_id>
```

---

## Kiến Trúc Vòng Đời Tích Hợp Antigravity

SaveToken giao tiếp trực tiếp với Google Antigravity qua file cấu hình `<plugin_dir>/hooks.json`:

```
Google Antigravity
    │
    ├── SessionStart   ──► Bơm các fact micro-skills đã học của repository
    ├── PreInvocation  ──► Kiểm tra ngân sách token và cảnh báo loop guard
    ├── PreToolUse     ──► Kiểm soát chặn các công cụ nằm trong danh sách cắt tỉa
    ├── PostToolUse    ──► Phân tích mã lỗi tool để phát hiện vòng lặp bế tắc
    └── Stop           ──► Ghi sổ cái số lượng token và tiền tiết kiệm được
```

Xem chi tiết kỹ thuật tại:
- [docs/ANTIGRAVITY_INTEGRATION.md](docs/ANTIGRAVITY_INTEGRATION.md) (Chi tiết cơ chế Hook)
- [docs/WINDOWS_SETUP.md](docs/WINDOWS_SETUP.md) (Hướng dẫn chi tiết cho Windows)
- [docs/BENCHMARKS.md](docs/BENCHMARKS.md) (Số liệu kiểm nghiệm thực tế)

---

## Chạy Bộ Kiểm Thử (Unit & Integration Tests)

Dự án đi kèm bộ hơn 550 bài kiểm thử tự động:

```bash
# Sử dụng pytest
python -m pytest tests/

# Sử dụng uv
uv run --with pytest pytest tests/
```

---

## Trích Dẫn Khoa Học

SaveToken kế thừa và phát triển từ công trình nghiên cứu gốc của Microsoft Research & UC Berkeley:

```bibtex
@article{li2026tokeneconomizer,
  title={TokenEconomizer: Active Cost and Loop Control for Agentic Coding},
  author={Li, Bo and et al.},
  journal={arXiv preprint arXiv:2610.22732},
  year={2026}
}
```

Mã nguồn dự án gốc: [https://github.com/microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer)

---

## Giấy Phép (License)

Dự án được phân phối dưới giấy phép nguồn mở [MIT License](LICENSE).
