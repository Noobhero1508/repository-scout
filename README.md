# Repository Scout

Repository Scout tự động tìm, lọc và xếp hạng các GitHub repository theo từng mục tiêu công việc. Hệ thống chạy mỗi ngày bằng GitHub Actions, không cần máy chủ riêng và không cần gói n8n trả phí.

## Hệ thống làm gì?

Mỗi ngày lúc khoảng **08:17 giờ Việt Nam**, workflow sẽ:

1. Đọc các nhóm tìm kiếm trong `config/jobs.json`.
2. Gọi GitHub Search API bằng token GitHub tự cấp cho workflow.
3. Loại repository bị archive và fork.
4. Chấm điểm theo độ liên quan, đà tăng stars, hoạt động, độ phổ biến, độ mới và tín hiệu tin cậy.
5. Ghi báo cáo mới nhất vào `reports/latest.md` và `reports/latest.json`.
6. Lưu một bản báo cáo theo ngày trong `reports/history/`.
7. Commit báo cáo trở lại repository để bạn xem lịch sử thay đổi.

Sau lần quét đầu tiên, hệ thống lưu số stars trong `data/state.json`. Các lần tiếp theo sẽ tính được mức tăng stars thực tế.

## Chi phí và tài khoản

- Cần một **tài khoản GitHub** và một repository để chạy workflow.
- Nên dùng **repository public** để standard GitHub-hosted runner được miễn phí.
- Không cần tạo Personal Access Token cho GitHub Actions; secret `GITHUB_TOKEN` được GitHub tạo tự động cho mỗi lần chạy.
- Nếu chạy trên máy cá nhân, token là tùy chọn nhưng nên có để tránh hạn mức API thấp.
- Không cần n8n, VPS, database hay dịch vụ trả phí.

Lưu ý: nội dung trong repository public, gồm cấu hình, state và báo cáo, sẽ được mọi người xem được. Không đặt token, email riêng hoặc dữ liệu nhạy cảm trong `config/jobs.json`.

## Đưa hệ thống lên GitHub

Tạo một repository public trống trên GitHub, sau đó tại thư mục dự án này chạy:

```powershell
git init
git add README.md .gitignore pyproject.toml config data repo_scout tests scripts reports .github
git commit -m "feat: add repository scout"
git branch -M main
git remote add origin https://github.com/TEN_CUA_BAN/TEN_REPOSITORY.git
git push -u origin main
```

Thay `TEN_CUA_BAN` và `TEN_REPOSITORY` bằng thông tin thật. Sau khi push:

1. Mở tab **Actions** trong repository.
2. Chọn **Repository Scout**.
3. Chọn **Run workflow** để chạy thử ngay, không cần đợi tới hôm sau.
4. Nếu bước lưu báo cáo báo lỗi quyền, vào **Settings → Actions → General → Workflow permissions**, chọn **Read and write permissions**, rồi chạy lại.

Việc tạo repository, đăng nhập, commit và push có tác động tới tài khoản GitHub nên chưa được chương trình tự thực hiện thay bạn.

## Chạy trên máy cá nhân

Yêu cầu Python 3.11 trở lên. Không cần cài package bên ngoài.

Chạy không có token:

```powershell
.\scripts\run-local.ps1
```

Chạy với token tạm thời trong phiên PowerShell hiện tại:

```powershell
$env:GITHUB_TOKEN = "github_pat_xxx"
.\scripts\run-local.ps1
```

Không ghi token trực tiếp vào code hoặc commit token lên GitHub. Để chỉ kiểm tra cấu hình mà không gọi mạng:

```powershell
python -m repo_scout --check-config
```

## Tùy chỉnh chủ đề tìm kiếm

Chỉnh `config/jobs.json`. Mỗi job có cấu trúc:

```json
{
  "id": "pdf_tools",
  "title": "Công cụ xử lý PDF",
  "description": "Thư viện đọc, trích xuất và chuyển đổi PDF.",
  "queries": [
    "pdf parser language:Python pushed:>={since} stars:>=20",
    "document extraction language:Python pushed:>={since} stars:>=20"
  ],
  "keywords": ["pdf", "parser", "document extraction", "ocr"],
  "preferred_languages": ["Python"],
  "top_n": 15
}
```

`{since}` được tự thay bằng ngày cách hiện tại `lookback_days`. Các qualifier như `stars:`, `language:`, `topic:`, `created:` và `pushed:` dùng cú pháp GitHub Search.

Các thiết lập quan trọng:

- `lookback_days`: khoảng thời gian quan tâm gần đây.
- `max_results_per_query`: số ứng viên lấy từ mỗi truy vấn; tối đa 100 trong cấu hình hiện tại.
- `report_top_n`: số kết quả mặc định cho mỗi nhóm.
- `exclude_archived` và `exclude_forks`: loại project không còn hoạt động hoặc bản fork.

## Cách tính điểm

Điểm từ 0–100 gồm:

| Thành phần | Trọng số |
|---|---:|
| Độ liên quan tới keywords và ngôn ngữ | 35% |
| Đà tăng stars | 20% |
| Hoạt động gần đây | 15% |
| Độ phổ biến | 15% |
| Độ mới | 10% |
| License, mô tả và topics | 5% |

Đây là điểm sàng lọc, không phải kết luận rằng một repository an toàn hoặc phù hợp tuyệt đối. Luôn kiểm tra source code, README, license, release và issue trước khi đưa vào dự án thật.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

