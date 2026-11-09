-- =====================================================
-- Schema Sprint 3: Kho nguyen lieu, cong thuc pha che, nha cung cap, nhap hang
-- Chay SAU schema.sql va schema_sprint2.sql.
-- Chay lai nhieu lan an toan: bang da co thi bo qua (KHONG xoa du lieu kho).
-- Quy tac: PK_, FK_, UQ_, CK_, DF_ | PK INT IDENTITY | DECIMAL cho tien va so luong
--
-- Moi thay doi ton kho DEU di qua LichSuKho (QD06):
--   LoaiGiaoDich: NHAP_HANG (+) | HUY_NHAP (-) | XUAT_KHO (-) | TIEU_HAO (-) | DIEU_CHINH (+/-)
-- Phieu nhap:  NHAP -> DA_NHAN (xac nhan, moi cong ton kho) | DA_HUY
-- =====================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- 12. Bang NguyenLieu
IF OBJECT_ID('dbo.NguyenLieu', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.NguyenLieu (
        NguyenLieuID INT IDENTITY(1,1) NOT NULL,
        TenNguyenLieu NVARCHAR(150) NOT NULL,
        DonViTinh NVARCHAR(30) NOT NULL,
        SoLuongTon DECIMAL(18,3) NOT NULL CONSTRAINT DF_NguyenLieu_SoLuongTon DEFAULT 0,
        MucTonToiThieu DECIMAL(18,3) NOT NULL CONSTRAINT DF_NguyenLieu_MucTonToiThieu DEFAULT 0,
        TrangThai BIT NOT NULL CONSTRAINT DF_NguyenLieu_TrangThai DEFAULT 1,
        NgayTao DATETIME2 NOT NULL CONSTRAINT DF_NguyenLieu_NgayTao DEFAULT SYSDATETIME(),
        NgayCapNhat DATETIME2 NULL,
        CONSTRAINT PK_NguyenLieu PRIMARY KEY (NguyenLieuID),
        CONSTRAINT UQ_NguyenLieu_TenNguyenLieu UNIQUE (TenNguyenLieu),
        CONSTRAINT CK_NguyenLieu_SoLuongTon CHECK (SoLuongTon >= 0),
        CONSTRAINT CK_NguyenLieu_MucTonToiThieu CHECK (MucTonToiThieu >= 0)
    );
END
GO

-- 13. Bang CongThuc (mon <-> nguyen lieu, dinh luong cho 1 phan)
IF OBJECT_ID('dbo.CongThuc', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CongThuc (
        CongThucID INT IDENTITY(1,1) NOT NULL,
        MonID INT NOT NULL,
        NguyenLieuID INT NOT NULL,
        SoLuongCan DECIMAL(18,3) NOT NULL,
        NgayCapNhat DATETIME2 NULL,
        CONSTRAINT PK_CongThuc PRIMARY KEY (CongThucID),
        CONSTRAINT UQ_CongThuc_Mon_NguyenLieu UNIQUE (MonID, NguyenLieuID),
        CONSTRAINT CK_CongThuc_SoLuongCan CHECK (SoLuongCan > 0),
        CONSTRAINT FK_CongThuc_Mon FOREIGN KEY (MonID) REFERENCES dbo.Mon(MonID),
        CONSTRAINT FK_CongThuc_NguyenLieu FOREIGN KEY (NguyenLieuID) REFERENCES dbo.NguyenLieu(NguyenLieuID)
    );
    CREATE INDEX IX_CongThuc_NguyenLieuID ON dbo.CongThuc(NguyenLieuID);
END
GO

-- Bang phu cua CongThuc: lich su thay doi cong thuc (API /recipes/{monId}/history).
-- Moi lan luu cong thuc ghi 1 dong chup lai TRUOC va SAU (JSON) de doi chieu gia von.
IF OBJECT_ID('dbo.CongThucLichSu', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CongThucLichSu (
        CongThucLichSuID INT IDENTITY(1,1) NOT NULL,
        MonID INT NOT NULL,
        TaiKhoanID INT NOT NULL,
        NgayThayDoi DATETIME2 NOT NULL CONSTRAINT DF_CongThucLichSu_NgayThayDoi DEFAULT SYSDATETIME(),
        TruocJson NVARCHAR(MAX) NULL,
        SauJson NVARCHAR(MAX) NOT NULL,
        LyDo NVARCHAR(500) NULL,
        CONSTRAINT PK_CongThucLichSu PRIMARY KEY (CongThucLichSuID),
        CONSTRAINT CK_CongThucLichSu_TruocJson CHECK (TruocJson IS NULL OR ISJSON(TruocJson) = 1),
        CONSTRAINT CK_CongThucLichSu_SauJson CHECK (ISJSON(SauJson) = 1),
        CONSTRAINT FK_CongThucLichSu_Mon FOREIGN KEY (MonID) REFERENCES dbo.Mon(MonID),
        CONSTRAINT FK_CongThucLichSu_TaiKhoan FOREIGN KEY (TaiKhoanID) REFERENCES dbo.TaiKhoan(TaiKhoanID)
    );
    CREATE INDEX IX_CongThucLichSu_MonID ON dbo.CongThucLichSu(MonID);
END
GO

-- 15. Bang NhaCungCap
IF OBJECT_ID('dbo.NhaCungCap', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.NhaCungCap (
        NhaCungCapID INT IDENTITY(1,1) NOT NULL,
        TenNhaCungCap NVARCHAR(150) NOT NULL,
        SoDienThoai VARCHAR(15) NULL,
        Email VARCHAR(255) NULL,
        DiaChi NVARCHAR(255) NULL,
        TrangThai BIT NOT NULL CONSTRAINT DF_NhaCungCap_TrangThai DEFAULT 1,
        NgayTao DATETIME2 NOT NULL CONSTRAINT DF_NhaCungCap_NgayTao DEFAULT SYSDATETIME(),
        NgayCapNhat DATETIME2 NULL,
        CONSTRAINT PK_NhaCungCap PRIMARY KEY (NhaCungCapID),
        CONSTRAINT UQ_NhaCungCap_TenNhaCungCap UNIQUE (TenNhaCungCap)
    );
END
GO

-- 16. Bang PhieuNhap
IF OBJECT_ID('dbo.PhieuNhap', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.PhieuNhap (
        PhieuNhapID INT IDENTITY(1,1) NOT NULL,
        NhaCungCapID INT NOT NULL,
        TaiKhoanID INT NOT NULL,
        MaPhieuNhap VARCHAR(30) NOT NULL,
        NgayNhap DATETIME2 NOT NULL CONSTRAINT DF_PhieuNhap_NgayNhap DEFAULT SYSDATETIME(),
        TongTien DECIMAL(18,2) NOT NULL CONSTRAINT DF_PhieuNhap_TongTien DEFAULT 0,
        TrangThai VARCHAR(30) NOT NULL CONSTRAINT DF_PhieuNhap_TrangThai DEFAULT 'NHAP',
        GhiChu NVARCHAR(500) NULL,
        NgayXacNhan DATETIME2 NULL,
        TaiKhoanXacNhanID INT NULL,
        LyDoHuy NVARCHAR(500) NULL,
        NgayCapNhat DATETIME2 NULL,
        CONSTRAINT PK_PhieuNhap PRIMARY KEY (PhieuNhapID),
        CONSTRAINT UQ_PhieuNhap_MaPhieuNhap UNIQUE (MaPhieuNhap),
        CONSTRAINT CK_PhieuNhap_TongTien CHECK (TongTien >= 0),
        CONSTRAINT CK_PhieuNhap_TrangThai CHECK (TrangThai IN ('NHAP', 'DA_NHAN', 'DA_HUY')),
        CONSTRAINT CK_PhieuNhap_LyDoHuy CHECK (TrangThai <> 'DA_HUY' OR LyDoHuy IS NOT NULL),
        CONSTRAINT FK_PhieuNhap_NhaCungCap FOREIGN KEY (NhaCungCapID) REFERENCES dbo.NhaCungCap(NhaCungCapID),
        CONSTRAINT FK_PhieuNhap_TaiKhoan FOREIGN KEY (TaiKhoanID) REFERENCES dbo.TaiKhoan(TaiKhoanID),
        CONSTRAINT FK_PhieuNhap_TaiKhoanXacNhan FOREIGN KEY (TaiKhoanXacNhanID) REFERENCES dbo.TaiKhoan(TaiKhoanID)
    );
    CREATE INDEX IX_PhieuNhap_NhaCungCapID ON dbo.PhieuNhap(NhaCungCapID);
    CREATE INDEX IX_PhieuNhap_NgayNhap ON dbo.PhieuNhap(NgayNhap);
    CREATE INDEX IX_PhieuNhap_TrangThai ON dbo.PhieuNhap(TrangThai);
END
GO

-- 17. Bang ChiTietPhieuNhap
IF OBJECT_ID('dbo.ChiTietPhieuNhap', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ChiTietPhieuNhap (
        ChiTietPhieuNhapID INT IDENTITY(1,1) NOT NULL,
        PhieuNhapID INT NOT NULL,
        NguyenLieuID INT NOT NULL,
        SoLuong DECIMAL(18,3) NOT NULL,
        DonGiaNhap DECIMAL(18,2) NOT NULL,
        ThanhTien DECIMAL(18,2) NOT NULL,
        CONSTRAINT PK_ChiTietPhieuNhap PRIMARY KEY (ChiTietPhieuNhapID),
        CONSTRAINT UQ_ChiTietPhieuNhap_Phieu_NguyenLieu UNIQUE (PhieuNhapID, NguyenLieuID),
        CONSTRAINT CK_ChiTietPhieuNhap_SoLuong CHECK (SoLuong > 0),
        CONSTRAINT CK_ChiTietPhieuNhap_DonGiaNhap CHECK (DonGiaNhap >= 0),
        CONSTRAINT CK_ChiTietPhieuNhap_ThanhTien CHECK (ThanhTien >= 0),
        CONSTRAINT FK_ChiTietPhieuNhap_PhieuNhap FOREIGN KEY (PhieuNhapID) REFERENCES dbo.PhieuNhap(PhieuNhapID),
        CONSTRAINT FK_ChiTietPhieuNhap_NguyenLieu FOREIGN KEY (NguyenLieuID) REFERENCES dbo.NguyenLieu(NguyenLieuID)
    );
    CREATE INDEX IX_ChiTietPhieuNhap_NguyenLieuID ON dbo.ChiTietPhieuNhap(NguyenLieuID);
END
GO

-- 14. Bang LichSuKho (moi lan nhap / xuat / dieu chinh / tieu hao)
-- Tao SAU PhieuNhap va DonHang vi co khoa ngoai toi hai bang nay.
IF OBJECT_ID('dbo.LichSuKho', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.LichSuKho (
        LichSuKhoID INT IDENTITY(1,1) NOT NULL,
        NguyenLieuID INT NOT NULL,
        TaiKhoanID INT NOT NULL,
        LoaiGiaoDich VARCHAR(30) NOT NULL,
        SoLuongThayDoi DECIMAL(18,3) NOT NULL,
        SoLuongTruoc DECIMAL(18,3) NOT NULL,
        SoLuongSau DECIMAL(18,3) NOT NULL,
        LyDo NVARCHAR(500) NULL,
        NgayGiaoDich DATETIME2 NOT NULL CONSTRAINT DF_LichSuKho_NgayGiaoDich DEFAULT SYSDATETIME(),
        DonHangID INT NULL,
        PhieuNhapID INT NULL,
        CONSTRAINT PK_LichSuKho PRIMARY KEY (LichSuKhoID),
        CONSTRAINT CK_LichSuKho_LoaiGiaoDich CHECK (LoaiGiaoDich IN ('NHAP_HANG', 'HUY_NHAP', 'XUAT_KHO', 'TIEU_HAO', 'DIEU_CHINH')),
        CONSTRAINT CK_LichSuKho_KhacKhong CHECK (SoLuongThayDoi <> 0),
        CONSTRAINT CK_LichSuKho_Dau CHECK (
            (LoaiGiaoDich = 'NHAP_HANG' AND SoLuongThayDoi > 0)
            OR (LoaiGiaoDich IN ('HUY_NHAP', 'XUAT_KHO', 'TIEU_HAO') AND SoLuongThayDoi < 0)
            OR LoaiGiaoDich = 'DIEU_CHINH'),
        CONSTRAINT CK_LichSuKho_Cong CHECK (SoLuongSau = SoLuongTruoc + SoLuongThayDoi AND SoLuongSau >= 0),
        CONSTRAINT CK_LichSuKho_LyDo CHECK (LoaiGiaoDich NOT IN ('DIEU_CHINH', 'XUAT_KHO') OR LyDo IS NOT NULL),
        CONSTRAINT FK_LichSuKho_NguyenLieu FOREIGN KEY (NguyenLieuID) REFERENCES dbo.NguyenLieu(NguyenLieuID),
        CONSTRAINT FK_LichSuKho_TaiKhoan FOREIGN KEY (TaiKhoanID) REFERENCES dbo.TaiKhoan(TaiKhoanID),
        CONSTRAINT FK_LichSuKho_DonHang FOREIGN KEY (DonHangID) REFERENCES dbo.DonHang(DonHangID),
        CONSTRAINT FK_LichSuKho_PhieuNhap FOREIGN KEY (PhieuNhapID) REFERENCES dbo.PhieuNhap(PhieuNhapID)
    );
    CREATE INDEX IX_LichSuKho_NguyenLieuID ON dbo.LichSuKho(NguyenLieuID, NgayGiaoDich);
    CREATE INDEX IX_LichSuKho_NgayGiaoDich ON dbo.LichSuKho(NgayGiaoDich);
    CREATE INDEX IX_LichSuKho_DonHangID ON dbo.LichSuKho(DonHangID) WHERE DonHangID IS NOT NULL;
    CREATE INDEX IX_LichSuKho_PhieuNhapID ON dbo.LichSuKho(PhieuNhapID) WHERE PhieuNhapID IS NOT NULL;
    -- Moi (don, nguyen lieu) chi tru kho tieu hao 1 lan -> chong ghi nhan trung o muc CSDL.
    CREATE UNIQUE INDEX UQ_LichSuKho_TieuHao_Don_NguyenLieu ON dbo.LichSuKho(DonHangID, NguyenLieuID)
        WHERE LoaiGiaoDich = 'TIEU_HAO';
END
GO
