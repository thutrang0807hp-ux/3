# SceneForge .51 — bỏ riêng --duration 8

Cập nhật từ bản .50. Gói chỉ thay `app/local_engine/flow_gflow_cli.py`.
Thay đổi duy nhất trong mã chạy: bỏ hai đối số `--duration`, `8` khỏi lệnh CLI,
để Flow dùng thời lượng mặc định. Các đối số và bước xử lý khác giữ nguyên.

Đã xác minh tệp trích từ EXE, checksum và bốn kiểm tra CLI cục bộ. Chưa xác minh
Windows/Flow thật. Không thay gói nguồn .50 đã cung cấp trước đó.

SHA256 EXE: `353ecf21f827d506592a9a71e4f39f4bc591b638652604d9c97e4961863db40d`
