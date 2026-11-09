"""Danh mục mẫu dùng riêng cho công cụ tạo dữ liệu Sprint 3.

Đơn vị g/ml giúp định lượng công thức và đơn giá nhập cùng một đơn vị.
Mỗi nguyên liệu: tên, đơn vị, mức tồn tối thiểu, giá nhập/đơn vị.
"""

NGUYEN_LIEU = [
    ("Cà phê Robusta", "g", 1000, "0.18"),
    ("Cà phê Arabica", "g", 800, "0.32"),
    ("Sữa đặc", "ml", 2000, "0.055"),
    ("Sữa tươi", "ml", 5000, "0.035"),
    ("Đường cát", "g", 2000, "0.025"),
    ("Đá viên", "g", 10000, "0.002"),
    ("Trà lài", "g", 300, "0.22"),
    ("Trà đen", "g", 300, "0.20"),
    ("Trà ô long", "g", 300, "0.35"),
    ("Bột matcha", "g", 200, "0.85"),
    ("Bột cacao", "g", 300, "0.28"),
    ("Bột chocolate", "g", 300, "0.30"),
    ("Kem béo", "ml", 1500, "0.09"),
    ("Kem whipping", "ml", 1000, "0.13"),
    ("Sữa yến mạch", "ml", 2000, "0.065"),
    ("Sữa dừa", "ml", 1500, "0.045"),
    ("Syrup vanilla", "ml", 500, "0.16"),
    ("Syrup caramel", "ml", 500, "0.16"),
    ("Syrup hazelnut", "ml", 500, "0.18"),
    ("Syrup đào", "ml", 800, "0.12"),
    ("Syrup vải", "ml", 800, "0.12"),
    ("Syrup dâu", "ml", 800, "0.12"),
    ("Syrup bạc hà", "ml", 500, "0.14"),
    ("Mật ong", "ml", 500, "0.15"),
    ("Chanh tươi", "g", 1500, "0.03"),
    ("Cam tươi", "g", 3000, "0.04"),
    ("Đào ngâm", "g", 1000, "0.08"),
    ("Vải ngâm", "g", 1000, "0.085"),
    ("Dâu tây", "g", 1000, "0.12"),
    ("Xoài chín", "g", 1500, "0.045"),
    ("Bơ sáp", "g", 1500, "0.06"),
    ("Chuối", "g", 1000, "0.025"),
    ("Chanh dây", "g", 1000, "0.045"),
    ("Dưa hấu", "g", 2000, "0.018"),
    ("Táo", "g", 2000, "0.055"),
    ("Sữa chua", "g", 1500, "0.05"),
    ("Trân châu đen", "g", 1000, "0.055"),
    ("Thạch trái cây", "g", 1000, "0.045"),
    ("Hạt chia", "g", 200, "0.16"),
    ("Muối biển", "g", 100, "0.02"),
    ("Phô mai kem", "g", 500, "0.18"),
    ("Bánh quy Oreo", "g", 800, "0.09"),
    ("Soda", "ml", 3000, "0.02"),
    ("Ly giấy", "cái", 200, "1200"),
    ("Ống hút giấy", "cái", 200, "300"),
    ("Túi mang đi", "cái", 100, "800"),
    ("Bột khoai môn cũ", "g", 200, "0.15"),
    ("Syrup hoa hồng cũ", "ml", 300, "0.18"),
]

# Giá tiền phía trên tính bằng nghìn đồng với g/ml; chuyển sang đồng khi nhập.
# Bao bì đã có đơn giá bằng đồng.

# Mỗi nhóm: tên nhóm và các món (tên, giá bán, {nguyên liệu: định lượng}).
THUC_DON = [
    ("Cà phê phin", [
        ("Cà phê đen đá", 25000, {"Cà phê Robusta": 25, "Đường cát": 15, "Đá viên": 150}),
        ("Cà phê sữa đá", 29000, {"Cà phê Robusta": 25, "Sữa đặc": 35, "Đá viên": 150}),
        ("Bạc xỉu", 32000, {"Cà phê Robusta": 15, "Sữa đặc": 25, "Sữa tươi": 100, "Đá viên": 150}),
        ("Cà phê muối", 39000, {"Cà phê Robusta": 25, "Sữa đặc": 25, "Kem béo": 30, "Muối biển": 1}),
        ("Cà phê cốt dừa", 45000, {"Cà phê Robusta": 25, "Sữa dừa": 80, "Sữa đặc": 25, "Đá viên": 150}),
    ]),
    ("Cà phê máy", [
        ("Espresso", 30000, {"Cà phê Arabica": 18}),
        ("Americano", 35000, {"Cà phê Arabica": 18, "Đá viên": 150}),
        ("Latte", 45000, {"Cà phê Arabica": 18, "Sữa tươi": 180}),
        ("Cappuccino", 45000, {"Cà phê Arabica": 18, "Sữa tươi": 150, "Bột cacao": 2}),
        ("Caramel macchiato", 49000, {"Cà phê Arabica": 18, "Sữa tươi": 160, "Syrup caramel": 20}),
    ]),
    ("Trà trái cây", [
        ("Trà đào cam", 39000, {"Trà đen": 8, "Syrup đào": 25, "Đào ngâm": 40, "Cam tươi": 30, "Đá viên": 180}),
        ("Trà vải", 39000, {"Trà lài": 8, "Syrup vải": 25, "Vải ngâm": 40, "Đá viên": 180}),
        ("Trà dâu", 42000, {"Trà lài": 8, "Syrup dâu": 25, "Dâu tây": 40, "Đá viên": 180}),
        ("Trà chanh mật ong", 35000, {"Trà lài": 8, "Chanh tươi": 30, "Mật ong": 25, "Đá viên": 180}),
        ("Trà chanh dây", 39000, {"Trà đen": 8, "Chanh dây": 50, "Đường cát": 25, "Đá viên": 180}),
    ]),
    ("Trà sữa", [
        ("Trà sữa truyền thống", 35000, {"Trà đen": 10, "Sữa tươi": 100, "Kem béo": 30, "Đường cát": 25, "Đá viên": 150}),
        ("Trà sữa ô long", 39000, {"Trà ô long": 10, "Sữa tươi": 100, "Kem béo": 30, "Đường cát": 25}),
        ("Trà sữa trân châu", 42000, {"Trà đen": 10, "Sữa tươi": 100, "Trân châu đen": 50, "Sữa đặc": 30}),
        ("Trà sữa thạch trái cây", 42000, {"Trà lài": 10, "Sữa tươi": 100, "Thạch trái cây": 50, "Đường cát": 25}),
        ("Ô long kem phô mai", 49000, {"Trà ô long": 10, "Phô mai kem": 25, "Kem whipping": 30, "Đường cát": 25}),
    ]),
    ("Matcha và cacao", [
        ("Matcha latte", 45000, {"Bột matcha": 5, "Sữa tươi": 180, "Sữa đặc": 25}),
        ("Matcha yến mạch", 49000, {"Bột matcha": 5, "Sữa yến mạch": 180, "Syrup vanilla": 20}),
        ("Cacao sữa nóng", 39000, {"Bột cacao": 15, "Sữa tươi": 180, "Sữa đặc": 25}),
        ("Chocolate đá", 45000, {"Bột chocolate": 20, "Sữa tươi": 150, "Kem whipping": 20, "Đá viên": 180}),
        ("Mocha hazelnut", 49000, {"Cà phê Arabica": 18, "Bột cacao": 10, "Sữa tươi": 150, "Syrup hazelnut": 20}),
    ]),
    ("Sinh tố", [
        ("Sinh tố bơ", 45000, {"Bơ sáp": 150, "Sữa tươi": 80, "Sữa đặc": 30, "Đá viên": 150}),
        ("Sinh tố xoài", 45000, {"Xoài chín": 150, "Sữa tươi": 80, "Sữa đặc": 30, "Đá viên": 150}),
        ("Sinh tố dâu", 49000, {"Dâu tây": 120, "Sữa tươi": 100, "Sữa đặc": 30, "Đá viên": 150}),
        ("Sinh tố chuối cacao", 45000, {"Chuối": 120, "Bột cacao": 10, "Sữa tươi": 100, "Đá viên": 150}),
        ("Oreo đá xay", 49000, {"Bánh quy Oreo": 40, "Sữa tươi": 120, "Kem whipping": 30, "Đá viên": 180}),
    ]),
    ("Nước ép", [
        ("Nước cam", 39000, {"Cam tươi": 300, "Đường cát": 15, "Đá viên": 100}),
        ("Nước ép dưa hấu", 35000, {"Dưa hấu": 300, "Đá viên": 100}),
        ("Nước ép táo", 45000, {"Táo": 250, "Đá viên": 100}),
        ("Chanh tươi hạt chia", 35000, {"Chanh tươi": 50, "Hạt chia": 5, "Đường cát": 25, "Đá viên": 150}),
        ("Cam mật ong", 45000, {"Cam tươi": 250, "Mật ong": 25, "Đá viên": 100}),
    ]),
    ("Soda và sữa chua", [
        ("Soda bạc hà", 39000, {"Soda": 180, "Syrup bạc hà": 25, "Chanh tươi": 20, "Đá viên": 150}),
        ("Soda dâu", 39000, {"Soda": 180, "Syrup dâu": 25, "Dâu tây": 30, "Đá viên": 150}),
        ("Sữa chua xoài", 42000, {"Sữa chua": 100, "Xoài chín": 100, "Sữa đặc": 20}),
        ("Sữa chua dâu", 42000, {"Sữa chua": 100, "Dâu tây": 80, "Sữa đặc": 20}),
        ("Sữa chua chanh dây", 42000, {"Sữa chua": 100, "Chanh dây": 50, "Sữa đặc": 20}),
    ]),
]

NHA_CUNG_CAP = [
    "Cà phê Cao Nguyên", "Cà phê Đà Lạt", "Sữa và Kem An Phú",
    "Trà Bảo Lộc", "Nguyên liệu Pha Chế Việt", "Syrup Hương Việt",
    "Trái cây Miền Tây", "Nông sản Đà Lạt", "Bao bì Xanh",
    "Đá sạch Bình Minh", "Thực phẩm Minh Tâm", "Sữa Hạt An Nhiên",
    "Bánh và Topping Hạnh Phúc", "Nguyên liệu Hương Xưa",
]

NHAN_SU = [
    ("admin", "Nguyễn Minh Anh", 1),
    ("quanly", "Trần Hoàng Nam", 2),
    ("thungan", "Lê Thu Hà", 3),
    ("phache", "Phạm Bảo Ngọc", 3),
    ("phucvu", "Võ Gia Huy", 3),
    ("tamnghi", "Đặng Thảo Vy", 3),
]
