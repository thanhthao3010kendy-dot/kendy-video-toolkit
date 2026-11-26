"""Sinh các tệp từ điển JSON. Sửa danh sách ở đây rồi chạy lại: .venv/bin/python tu-dien/tao_tu_dien.py

Quy ước nguồn (giữ đúng ký hiệu của Kendy):
  C   – kiến thức chung, cách viết phổ biến, CHỜ KENDY XÁC NHẬN cách viết.
  UD  – cách viết đang dùng trong ứng dụng Bát Tự của Kendy (kho Kendy-tarot, src/core, src/engine).
Từ điển chỉ phục vụ CHÍNH TẢ phụ đề. Không phải lý pháp, không dùng để luận giải."""
import json
from pathlib import Path

D = Path(__file__).resolve().parent
TT = "Chờ Kendy xác nhận cách viết"


def muc(chuan, nhom, nguon="C", khac=None):
    m = {"chuan": chuan, "nhom": nhom, "nguon": nguon}
    if khac:
        m["khac"] = khac
    return m


def save(name, ten, muc_list, goi_y, ghi_chu=""):
    data = {"linh_vuc": name, "ten": ten, "trang_thai": TT, "ghi_chu": ghi_chu,
            "goi_y_whisper": goi_y, "muc": muc_list}
    (D / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(name, len(muc_list))


# ---------------- Tarot: 22 Ẩn Chính + 56 Ẩn Phụ = 78 lá
MAJOR = [("The Fool", "Chàng Khờ"), ("The Magician", "Nhà Ảo Thuật"), ("The High Priestess", "Nữ Tư Tế"),
         ("The Empress", "Hoàng Hậu"), ("The Emperor", "Hoàng Đế"), ("The Hierophant", "Giáo Hoàng"),
         ("The Lovers", "Tình Nhân"), ("The Chariot", "Cỗ Xe"), ("Strength", "Sức Mạnh"), ("The Hermit", "Ẩn Sĩ"),
         ("Wheel of Fortune", "Bánh Xe Số Phận"), ("Justice", "Công Lý"), ("The Hanged Man", "Người Treo Ngược"),
         ("Death", "Cái Chết"), ("Temperance", "Tiết Chế"), ("The Devil", "Ác Quỷ"), ("The Tower", "Tòa Tháp"),
         ("The Star", "Ngôi Sao"), ("The Moon", "Mặt Trăng"), ("The Sun", "Mặt Trời"), ("Judgement", "Phán Xét"),
         ("The World", "Thế Giới")]
SUITS = [("Wands", "Gậy"), ("Cups", "Cốc"), ("Swords", "Kiếm"), ("Pentacles", "Tiền")]
RANKS = [("Ace", "Át"), ("Two", "Hai"), ("Three", "Ba"), ("Four", "Bốn"), ("Five", "Năm"), ("Six", "Sáu"),
         ("Seven", "Bảy"), ("Eight", "Tám"), ("Nine", "Chín"), ("Ten", "Mười"), ("Page", "Tiểu Đồng"),
         ("Knight", "Hiệp Sĩ"), ("Queen", "Nữ Hoàng"), ("King", "Vua")]
tarot = []
for i, (en, vi) in enumerate(MAJOR):
    tarot.append(muc(vi, f"Ẩn Chính {i}", khac=[en]))
for se, sv in SUITS:
    for re_, rv in RANKS:
        tarot.append(muc(f"{rv} {sv}", f"Ẩn Phụ – {sv}", khac=[f"{re_} of {se}"]))
tarot += [muc(t, "thuật ngữ") for t in [
    "Ẩn Chính", "Ẩn Phụ", "Bộ Gậy", "Bộ Cốc", "Bộ Kiếm", "Bộ Tiền", "lá ngược", "lá xuôi", "trải bài",
    "rút bài", "thông điệp", "năng lượng", "Rider Waite", "Oracle", "lá bài chủ đạo", "tụ bài", "xào bài"]]
assert sum(1 for m in tarot if m["nhom"].startswith("Ẩn")) == 78
save("tarot", "Tarot – 78 lá và thuật ngữ", tarot,
     ["Tarot", "Ẩn Chính", "Ẩn Phụ", "Gậy", "Cốc", "Kiếm", "Tiền", "trải bài", "lá ngược", "The Fool", "The Moon",
      "Ace of Cups", "Tiểu Đồng", "Hiệp Sĩ", "Nữ Hoàng"],
     "Tên tiếng Việt là cách gọi phổ biến; Kendy chọn cách gọi riêng (ví dụ Tiền / Tiền Xu / Ngũ Giác) thì sửa ở đây.")

# ---------------- Tứ Trụ Bát Tự Manh Phái (cách viết theo ứng dụng Bát Tự của Kendy)
CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
mp = [muc(c, "Thiên Can", "UD") for c in CAN] + [muc(c, "Địa Chi", "UD") for c in CHI]
mp += [muc(f"{CAN[i % 10]} {CHI[i % 12]}", "Lục Thập Hoa Giáp", "UD") for i in range(60)]
mp += [muc(t, "Ngũ Hành", "UD") for t in ["Mộc", "Hỏa", "Thổ", "Kim", "Thủy"]]
mp += [muc(t, "Thập Thần", "UD") for t in ["Tỷ Kiên", "Kiếp Tài", "Thực Thần", "Thương Quan", "Thiên Tài", "Chính Tài",
                                           "Thất Sát", "Chính Quan", "Thiên Ấn", "Chính Ấn", "Tỷ Kiếp", "Thực Thương",
                                           "Tài Tinh", "Quan Sát", "Ấn Tinh", "Nhật Chủ", "Nhật Can"]]
mp += [muc(t, "Tàng can / trụ", "UD") for t in ["Tàng can", "Chính khí", "Trung khí", "Dư khí", "Trụ Năm", "Trụ Tháng",
                                                "Trụ Ngày", "Trụ Giờ", "Cung vị", "Môn hộ", "Chủ vị", "Tân vị",
                                                "Nạp âm"]]
mp += [muc(t, "Quan hệ", "UD") for t in ["Thiên Can Ngũ Hợp", "Lục Hợp", "Tam Hợp", "Tam Hội", "Lục Xung", "Tương Hình",
                                         "Tự Hình", "Lục Hại", "Lục Phá", "Mộ", "Khố", "Mộ Khố", "Lộc", "Dương Nhận",
                                         "Không vong", "Phục ngâm", "Phản ngâm"]]
mp += [muc(t, "Lý pháp Manh Phái", "UD") for t in ["Manh Phái", "Thể – Dụng", "Thể Dụng", "Tố Công", "Hư – Thực", "Hư Thực",
                                                   "Chủ – Khách", "Đảng Thế", "Đăng thế", "Khóa Công", "Công Thần",
                                                   "Công Xưởng", "Tượng pháp", "Phá công", "Lộc Thần", "Nguyên Thần",
                                                   "Đại vận", "Lưu niên", "Lưu nguyệt", "Ứng kỳ", "Thế trận"]]
mp += [muc(t, "Thần sát", "UD") for t in ["Thiên Ất Quý Nhân", "Văn Xương", "Đào Hoa", "Dịch Mã", "Hoa Cái"]]
save("bat-tu-manh-phai", "Tứ Trụ Bát Tự Manh Phái", mp,
     ["Bát Tự", "Tứ Trụ", "Manh Phái", "Thể Dụng", "Tố Công", "Hư Thực", "Đảng Thế", "Nhật Chủ", "Thất Sát",
      "Thương Quan", "Kiếp Tài", "Đại vận", "Lưu niên", "Ứng kỳ", "Tỵ", "Mão", "Dậu"],
     "Nguồn UD: cách viết đang dùng trong ứng dụng Bát Tự v121 của Kendy. 'Đăng thế / Đảng Thế' giữ cả hai cách "
     "viết vì đang CHỜ KENDY XÁC NHẬN. Từ điển chỉ phục vụ chính tả phụ đề, không mang nội dung lý pháp.")

# ---------------- Tử Vi
tv = [muc(t, "14 Chính tinh") for t in ["Tử Vi", "Thiên Cơ", "Thái Dương", "Vũ Khúc", "Thiên Đồng", "Liêm Trinh",
                                         "Thiên Phủ", "Thái Âm", "Tham Lang", "Cự Môn", "Thiên Tướng", "Thiên Lương",
                                         "Thất Sát", "Phá Quân"]]
tv += [muc(f"cung {t}", "12 cung", khac=[t]) for t in ["Mệnh", "Phụ Mẫu", "Phúc Đức", "Điền Trạch", "Quan Lộc",
                                                       "Nô Bộc", "Thiên Di", "Tật Ách", "Tài Bạch", "Tử Tức",
                                                       "Phu Thê", "Huynh Đệ", "Thân"]]
tv += [muc(t, "Phụ tinh / Tứ Hóa") for t in ["Văn Xương", "Văn Khúc", "Tả Phù", "Hữu Bật", "Thiên Khôi", "Thiên Việt",
                                             "Lộc Tồn", "Thiên Mã", "Hóa Lộc", "Hóa Quyền", "Hóa Khoa", "Hóa Kỵ",
                                             "Kình Dương", "Đà La", "Hỏa Tinh", "Linh Tinh", "Địa Không", "Địa Kiếp",
                                             "Tuần Không", "Triệt Lộ", "Thiên Hình", "Thiên Diêu", "Hồng Loan",
                                             "Thiên Hỷ", "Đào Hoa", "Cô Thần", "Quả Tú", "Thái Tuế"]]
tv += [muc(t, "Vòng Tràng Sinh") for t in ["Tràng Sinh", "Mộc Dục", "Quan Đới", "Lâm Quan", "Đế Vượng", "Suy", "Bệnh",
                                           "Tử", "Mộ", "Tuyệt", "Thai", "Dưỡng"]]
tv += [muc(t, "Cục / thuật ngữ") for t in ["Thủy Nhị Cục", "Mộc Tam Cục", "Kim Tứ Cục", "Thổ Ngũ Cục", "Hỏa Lục Cục",
                                           "lá số Tử Vi", "an sao", "đại hạn", "tiểu hạn", "lưu niên", "tam phương tứ chính",
                                           "Mệnh Vô Chính Diệu", "Thân cư"]]
save("tu-vi", "Tử Vi Đẩu Số", tv,
     ["Tử Vi", "cung Mệnh", "Thiên Cơ", "Liêm Trinh", "Tham Lang", "Cự Môn", "Phá Quân", "Hóa Kỵ", "Hóa Lộc",
      "Kình Dương", "Đà La", "Địa Không", "Địa Kiếp", "đại hạn", "tiểu hạn"])

# ---------------- Phong Thủy
SON24 = ["Nhâm", "Tý", "Quý", "Sửu", "Cấn", "Dần", "Giáp", "Mão", "Ất", "Thìn", "Tốn", "Tỵ", "Bính", "Ngọ", "Đinh",
         "Mùi", "Khôn", "Thân", "Canh", "Dậu", "Tân", "Tuất", "Càn", "Hợi"]
pt = [muc(f"sơn {s}", "24 sơn", khac=[f"tọa {s}", f"hướng {s}"]) for s in SON24]
pt += [muc(t, "Bát Trạch") for t in ["Bát Trạch", "Đông Tứ Trạch", "Tây Tứ Trạch", "Đông Tứ Mệnh", "Tây Tứ Mệnh",
                                     "Sinh Khí", "Thiên Y", "Diên Niên", "Phục Vị", "Tuyệt Mệnh", "Ngũ Quỷ", "Lục Sát",
                                     "Họa Hại", "cung Phi", "quái số"]]
pt += [muc(t, "Huyền Không") for t in ["Huyền Không Phi Tinh", "Cửu Tinh", "Nhất Bạch", "Nhị Hắc", "Tam Bích", "Tứ Lục",
                                       "Ngũ Hoàng", "Lục Bạch", "Thất Xích", "Bát Bạch", "Cửu Tử", "vận 9", "Hạ Nguyên",
                                       "sơn tinh", "hướng tinh", "vượng sơn vượng hướng", "thượng sơn hạ thủy"]]
pt += [muc(t, "Loan đầu / thuật ngữ") for t in ["Thanh Long", "Bạch Hổ", "Chu Tước", "Huyền Vũ", "Minh Đường",
                                                "Long Mạch", "Huyệt", "La Kinh", "La Bàn", "tọa sơn", "lập hướng",
                                                "Tam Sát", "Thái Tuế", "Tuế Phá", "Lục Thập Tứ Quái", "kích hoạt",
                                                "hóa giải", "linh vật"]]
save("phong-thuy", "Phong Thủy", pt,
     ["Phong Thủy", "Bát Trạch", "Huyền Không Phi Tinh", "Ngũ Hoàng", "Nhị Hắc", "Sinh Khí", "Thiên Y", "Diên Niên",
      "Tuyệt Mệnh", "Ngũ Quỷ", "Thanh Long", "Bạch Hổ", "Minh Đường", "tọa", "hướng", "Tam Sát"])

# ---------------- Kinh Dịch: 8 quẻ đơn + 64 quẻ kép (tên Hán Việt thông dụng)
QUE = ["Thuần Càn", "Thuần Khôn", "Thủy Lôi Truân", "Sơn Thủy Mông", "Thủy Thiên Nhu", "Thiên Thủy Tụng",
       "Địa Thủy Sư", "Thủy Địa Tỷ", "Phong Thiên Tiểu Súc", "Thiên Trạch Lý", "Địa Thiên Thái", "Thiên Địa Bĩ",
       "Thiên Hỏa Đồng Nhân", "Hỏa Thiên Đại Hữu", "Địa Sơn Khiêm", "Lôi Địa Dự", "Trạch Lôi Tùy", "Sơn Phong Cổ",
       "Địa Trạch Lâm", "Phong Địa Quán", "Hỏa Lôi Phệ Hạp", "Sơn Hỏa Bí", "Sơn Địa Bác", "Địa Lôi Phục",
       "Thiên Lôi Vô Vọng", "Sơn Thiên Đại Súc", "Sơn Lôi Di", "Trạch Phong Đại Quá", "Thuần Khảm", "Thuần Ly",
       "Trạch Sơn Hàm", "Lôi Phong Hằng", "Thiên Sơn Độn", "Lôi Thiên Đại Tráng", "Hỏa Địa Tấn", "Địa Hỏa Minh Di",
       "Phong Hỏa Gia Nhân", "Hỏa Trạch Khuê", "Thủy Sơn Kiển", "Lôi Thủy Giải", "Sơn Trạch Tổn", "Phong Lôi Ích",
       "Trạch Thiên Quải", "Thiên Phong Cấu", "Trạch Địa Tụy", "Địa Phong Thăng", "Trạch Thủy Khốn", "Thủy Phong Tỉnh",
       "Trạch Hỏa Cách", "Hỏa Phong Đỉnh", "Thuần Chấn", "Thuần Cấn", "Phong Sơn Tiệm", "Lôi Trạch Quy Muội",
       "Lôi Hỏa Phong", "Hỏa Sơn Lữ", "Thuần Tốn", "Thuần Đoài", "Phong Thủy Hoán", "Thủy Trạch Tiết",
       "Phong Trạch Trung Phu", "Lôi Sơn Tiểu Quá", "Thủy Hỏa Ký Tế", "Hỏa Thủy Vị Tế"]
assert len(QUE) == 64
kd = [muc(t, "Bát Quái") for t in ["Càn", "Đoài", "Ly", "Chấn", "Tốn", "Khảm", "Cấn", "Khôn"]]
kd += [muc(q, f"Quẻ {i + 1}") for i, q in enumerate(QUE)]
kd += [muc(t, "thuật ngữ") for t in ["Kinh Dịch", "Chu Dịch", "Hà Đồ", "Lạc Thư", "Tiên Thiên Bát Quái",
                                     "Hậu Thiên Bát Quái", "quẻ Chủ", "quẻ Hỗ", "quẻ Biến", "hào động", "Thoán từ",
                                     "Hào từ", "Thập Dực", "Lục Hào", "Mai Hoa Dịch Số", "Dụng thần", "Thế ứng",
                                     "Lục Thân", "Lục Thú", "âm dương", "Thái Cực", "Lưỡng Nghi", "Tứ Tượng"]]
save("kinh-dich", "Kinh Dịch", kd,
     ["Kinh Dịch", "Bát Quái", "quẻ", "hào động", "Thuần Càn", "Thuần Khôn", "Địa Thiên Thái", "Thiên Địa Bĩ",
      "Thủy Hỏa Ký Tế", "Hỏa Thủy Vị Tế", "Mai Hoa Dịch Số", "Lục Hào", "Hà Đồ", "Lạc Thư"])

# ---------------- Nhân Tướng Học
nt = [muc(t, "Tam Đình / bộ vị") for t in ["Tam Đình", "Thượng Đình", "Trung Đình", "Hạ Đình", "Ngũ Quan", "Ngũ Nhạc",
                                          "Tứ Độc", "Thiên Đình", "Ấn Đường", "Sơn Căn", "Niên Thượng", "Thọ Thượng",
                                          "Chuẩn Đầu", "Lan Đài", "Đình Úy", "Nhân Trung", "Pháp Lệnh", "Địa Các",
                                          "Lưỡng Quyền", "Ngọa Tằm", "Lệ Đường", "Ngư Vĩ", "Gian Môn", "Thiên Thương",
                                          "Địa Khố", "Thừa Tương", "Biên Địa", "Nhật Giác", "Nguyệt Giác"]]
nt += [muc(t, "Thập nhị cung (tướng)") for t in ["cung Mệnh", "cung Tài Bạch", "cung Huynh Đệ", "cung Điền Trạch",
                                                 "cung Tử Tức", "cung Nô Bộc", "cung Thê Thiếp", "cung Tật Ách",
                                                 "cung Thiên Di", "cung Quan Lộc", "cung Phúc Đức", "cung Phụ Mẫu"]]
nt += [muc(t, "thuật ngữ") for t in ["Nhân Tướng Học", "Ma Y Thần Tướng", "Thần Tướng Toàn Biên", "khí sắc",
                                     "thần khí", "cốt tướng", "thủ tướng", "chỉ tay", "đường Sinh Đạo",
                                     "đường Trí Đạo", "đường Tâm Đạo", "đường Định Mệnh", "nốt ruồi", "Ngũ Hành hình tướng"]]
save("nhan-tuong", "Nhân Tướng Học", nt,
     ["Nhân Tướng Học", "Tam Đình", "Ấn Đường", "Sơn Căn", "Chuẩn Đầu", "Pháp Lệnh", "Nhân Trung", "Ngọa Tằm",
      "Lưỡng Quyền", "Địa Các", "khí sắc", "Ma Y Thần Tướng"])
