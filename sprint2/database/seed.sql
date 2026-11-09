-- =====================================================
-- Du lieu nen bat buoc: vai tro, quyen, gan quyen cho vai tro.
-- Chay lai sau moi lan them quyen moi (vd Sprint 2). Luu y: gan quyen ve mac dinh.
-- KHONG co tai khoan / nhom mon / mon mau.
-- Tao tai khoan dau tien:  py -3.12 tao_tai_khoan.py
-- Nhom mon va mon them tren giao dien (trang Thuc don).
-- =====================================================

-- Chuan hoa ten vai tro co dau tren CSDL da cai ban cu.
UPDATE dbo.VaiTro SET TenVaiTro = N'Quản trị viên' WHERE VaiTroID = 1;
UPDATE dbo.VaiTro SET TenVaiTro = N'Quản lý'       WHERE VaiTroID = 2;
UPDATE dbo.VaiTro SET TenVaiTro = N'Nhân viên'     WHERE VaiTroID = 3;
GO

-- Vai tro
SET IDENTITY_INSERT dbo.VaiTro ON;
MERGE INTO dbo.VaiTro AS t
USING (VALUES
    (1, N'Quản trị viên', N'Quản lý tài khoản, phân quyền, cấu hình hệ thống'),
    (2, N'Quản lý', N'Quản lý thực đơn, giá bán, kho, nhân viên, báo cáo'),
    (3, N'Nhân viên', N'Tiếp nhận gọi món, tạo đơn, thanh toán')
) AS s (VaiTroID, TenVaiTro, MoTa)
ON t.VaiTroID = s.VaiTroID
WHEN NOT MATCHED THEN INSERT (VaiTroID, TenVaiTro, MoTa, NgayTao)
    VALUES (s.VaiTroID, s.TenVaiTro, s.MoTa, SYSDATETIME());
SET IDENTITY_INSERT dbo.VaiTro OFF;
GO

-- Quyen
SET IDENTITY_INSERT dbo.Quyen ON;
MERGE INTO dbo.Quyen AS t
USING (VALUES
    (1, N'account.view', N'Xem danh sach tai khoan'),
    (2, N'account.create', N'Tao tai khoan'),
    (3, N'account.update', N'Cap nhat tai khoan'),
    (4, N'account.lock', N'Khoa/mo tai khoan'),
    (5, N'role.manage', N'Quan ly vai tro va phan quyen'),
    (6, N'menu.view', N'Xem danh muc va thuc don'),
    (7, N'menu.manage', N'Them/sua/xoa danh muc va mon'),
    -- Sprint 2
    (8, N'order.view', N'Xem don hang'),
    (9, N'order.manage', N'Tao don, sua mon trong don, cap nhat trang thai'),
    (10, N'order.cancel', N'Huy don hang'),
    (11, N'payment.manage', N'Thu tien, xac nhan thanh toan, xem va in hoa don'),
    (12, N'payment.refund', N'Hoan tien')
) AS s (QuyenID, TenQuyen, MoTa)
ON t.QuyenID = s.QuyenID
WHEN NOT MATCHED THEN INSERT (QuyenID, TenQuyen, MoTa)
    VALUES (s.QuyenID, s.TenQuyen, s.MoTa);
SET IDENTITY_INSERT dbo.Quyen OFF;
GO

-- Gan quyen cho vai tro
-- Quan tri vien: tat ca; Quan ly: tru role.manage;
-- Nhan vien: xem thuc don + ban hang (tao/xu ly/huy don, thu tien), KHONG hoan tien.
DELETE FROM dbo.VaiTroQuyen;
INSERT INTO dbo.VaiTroQuyen (VaiTroID, QuyenID) VALUES
    (1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11),(1,12),
    (2,1),(2,2),(2,3),(2,4),(2,6),(2,7),(2,8),(2,9),(2,10),(2,11),(2,12),
    (3,6),(3,8),(3,9),(3,10),(3,11);
GO
