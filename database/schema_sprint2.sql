-- =====================================================
-- Schema Sprint 2: Don hang, thanh toan, hoa don, hoan tien
-- Chay SAU schema.sql. Chi tao/xoa 5 bang Sprint 2, khong dung bang Sprint 1.
-- Quy tac: PK_, FK_, UQ_, CK_, DF_ | PK INT IDENTITY | DECIMAL cho tien
--
-- Trang thai don (xu ly) va trang thai thanh toan TACH RIENG:
--   DonHang.TrangThai  : MOI -> CHO_PHA_CHE -> DANG_PHA_CHE -> HOAN_THANH | DA_HUY
--   ThanhToan.TrangThai: CHO_XAC_NHAN -> THANH_CONG | THAT_BAI ; THANH_CONG -> HOAN_MOT_PHAN | DA_HOAN_TIEN
-- =====================================================

-- Bang Sprint 3 (LichSuKho) tro toi DonHang -> phai xoa truoc
IF OBJECT_ID('dbo.LichSuKho', 'U') IS NOT NULL DROP TABLE dbo.LichSuKho;
GO

-- Xoa theo thu tu FK nguoc
IF OBJECT_ID('dbo.HoanTien', 'U') IS NOT NULL DROP TABLE dbo.HoanTien;
IF OBJECT_ID('dbo.HoaDon', 'U') IS NOT NULL DROP TABLE dbo.HoaDon;
IF OBJECT_ID('dbo.ThanhToan', 'U') IS NOT NULL DROP TABLE dbo.ThanhToan;
IF OBJECT_ID('dbo.ChiTietDonHang', 'U') IS NOT NULL DROP TABLE dbo.ChiTietDonHang;
IF OBJECT_ID('dbo.DonHang', 'U') IS NOT NULL DROP TABLE dbo.DonHang;
GO

-- 7. Bang DonHang
CREATE TABLE dbo.DonHang (
    DonHangID INT IDENTITY(1,1) NOT NULL,
    TaiKhoanID INT NULL,
    MaDonHang VARCHAR(30) NOT NULL,
    ThoiGianDat DATETIME2 NOT NULL CONSTRAINT DF_DonHang_ThoiGianDat DEFAULT SYSDATETIME(),
    TongTien DECIMAL(18,2) NOT NULL CONSTRAINT DF_DonHang_TongTien DEFAULT 0,
    GiamGia DECIMAL(18,2) NOT NULL CONSTRAINT DF_DonHang_GiamGia DEFAULT 0,
    ThanhTien DECIMAL(18,2) NOT NULL CONSTRAINT DF_DonHang_ThanhTien DEFAULT 0,
    TrangThai VARCHAR(30) NOT NULL CONSTRAINT DF_DonHang_TrangThai DEFAULT 'MOI',
    GhiChu NVARCHAR(500) NULL,
    LyDoHuy NVARCHAR(500) NULL,
    NgayCapNhat DATETIME2 NULL,
    CONSTRAINT PK_DonHang PRIMARY KEY (DonHangID),
    CONSTRAINT UQ_DonHang_MaDonHang UNIQUE (MaDonHang),
    CONSTRAINT CK_DonHang_TrangThai CHECK (TrangThai IN ('MOI', 'CHO_PHA_CHE', 'DANG_PHA_CHE', 'HOAN_THANH', 'DA_HUY')),
    CONSTRAINT CK_DonHang_TongTien CHECK (TongTien >= 0),
    CONSTRAINT CK_DonHang_GiamGia CHECK (GiamGia >= 0 AND GiamGia <= TongTien),
    CONSTRAINT CK_DonHang_ThanhTien CHECK (ThanhTien >= 0),
    CONSTRAINT CK_DonHang_LyDoHuy CHECK (TrangThai <> 'DA_HUY' OR LyDoHuy IS NOT NULL),
    CONSTRAINT FK_DonHang_TaiKhoan FOREIGN KEY (TaiKhoanID) REFERENCES dbo.TaiKhoan(TaiKhoanID)
);
GO
CREATE INDEX IX_DonHang_TaiKhoanID ON dbo.DonHang(TaiKhoanID);
GO
CREATE INDEX IX_DonHang_ThoiGianDat ON dbo.DonHang(ThoiGianDat);
GO
CREATE INDEX IX_DonHang_TrangThai ON dbo.DonHang(TrangThai);
GO

-- 8. Bang ChiTietDonHang (luu TenMon, DonGia tai thoi diem dat)
CREATE TABLE dbo.ChiTietDonHang (
    ChiTietDonHangID INT IDENTITY(1,1) NOT NULL,
    DonHangID INT NOT NULL,
    MonID INT NOT NULL,
    TenMon NVARCHAR(150) NOT NULL,
    DonGia DECIMAL(18,2) NOT NULL,
    SoLuong INT NOT NULL,
    ThanhTien DECIMAL(18,2) NOT NULL,
    GhiChu NVARCHAR(255) NULL,
    CONSTRAINT PK_ChiTietDonHang PRIMARY KEY (ChiTietDonHangID),
    CONSTRAINT CK_ChiTietDonHang_DonGia CHECK (DonGia >= 0),
    CONSTRAINT CK_ChiTietDonHang_SoLuong CHECK (SoLuong > 0),
    CONSTRAINT CK_ChiTietDonHang_ThanhTien CHECK (ThanhTien = DonGia * SoLuong),
    CONSTRAINT FK_ChiTietDonHang_DonHang FOREIGN KEY (DonHangID) REFERENCES dbo.DonHang(DonHangID),
    CONSTRAINT FK_ChiTietDonHang_Mon FOREIGN KEY (MonID) REFERENCES dbo.Mon(MonID)
);
GO
CREATE INDEX IX_ChiTietDonHang_DonHangID ON dbo.ChiTietDonHang(DonHangID);
GO
CREATE INDEX IX_ChiTietDonHang_MonID ON dbo.ChiTietDonHang(MonID);
GO

-- Index loc (filtered index) can QUOTED_IDENTIFIER ON; sqlcmd mac dinh OFF.
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- 9. Bang ThanhToan (1 don co the co nhieu giao dich, vd that bai roi tra lai)
CREATE TABLE dbo.ThanhToan (
    ThanhToanID INT IDENTITY(1,1) NOT NULL,
    DonHangID INT NOT NULL,
    MaGiaoDich VARCHAR(100) NULL,
    PhuongThuc VARCHAR(30) NOT NULL,
    SoTien DECIMAL(18,2) NOT NULL,
    TrangThai VARCHAR(30) NOT NULL CONSTRAINT DF_ThanhToan_TrangThai DEFAULT 'CHO_XAC_NHAN',
    ThoiGianThanhToan DATETIME2 NULL,
    NgayTao DATETIME2 NOT NULL CONSTRAINT DF_ThanhToan_NgayTao DEFAULT SYSDATETIME(),
    CONSTRAINT PK_ThanhToan PRIMARY KEY (ThanhToanID),
    CONSTRAINT CK_ThanhToan_PhuongThuc CHECK (PhuongThuc IN ('TIEN_MAT', 'CHUYEN_KHOAN', 'THE')),
    CONSTRAINT CK_ThanhToan_SoTien CHECK (SoTien > 0),
    CONSTRAINT CK_ThanhToan_TrangThai CHECK (TrangThai IN ('CHO_XAC_NHAN', 'THANH_CONG', 'THAT_BAI', 'HOAN_MOT_PHAN', 'DA_HOAN_TIEN')),
    CONSTRAINT FK_ThanhToan_DonHang FOREIGN KEY (DonHangID) REFERENCES dbo.DonHang(DonHangID)
);
GO
-- UNIQUE nhung cho phep nhieu NULL (rang buoc UNIQUE thuong chi cho 1 NULL).
CREATE UNIQUE INDEX UQ_ThanhToan_MaGiaoDich ON dbo.ThanhToan(MaGiaoDich) WHERE MaGiaoDich IS NOT NULL;
GO
CREATE INDEX IX_ThanhToan_DonHangID ON dbo.ThanhToan(DonHangID);
GO
-- Chong thanh toan trung o muc CSDL: moi don chi co 1 giao dich chua that bai
-- (dang cho / thanh cong / da hoan). Giao dich that bai thi duoc tao lai.
CREATE UNIQUE INDEX UQ_ThanhToan_DonHang_HieuLuc ON dbo.ThanhToan(DonHangID)
    WHERE TrangThai IN ('CHO_XAC_NHAN', 'THANH_CONG', 'HOAN_MOT_PHAN', 'DA_HOAN_TIEN');
GO

-- 10. Bang HoaDon (1 don - 1 hoa don)
CREATE TABLE dbo.HoaDon (
    HoaDonID INT IDENTITY(1,1) NOT NULL,
    DonHangID INT NOT NULL,
    MaHoaDon VARCHAR(30) NOT NULL,
    NgayLap DATETIME2 NOT NULL CONSTRAINT DF_HoaDon_NgayLap DEFAULT SYSDATETIME(),
    TongTien DECIMAL(18,2) NOT NULL,
    GiamGia DECIMAL(18,2) NOT NULL CONSTRAINT DF_HoaDon_GiamGia DEFAULT 0,
    ThanhTien DECIMAL(18,2) NOT NULL,
    TrangThai VARCHAR(20) NOT NULL CONSTRAINT DF_HoaDon_TrangThai DEFAULT 'DA_THANH_TOAN',
    CONSTRAINT PK_HoaDon PRIMARY KEY (HoaDonID),
    CONSTRAINT UQ_HoaDon_DonHangID UNIQUE (DonHangID),
    CONSTRAINT UQ_HoaDon_MaHoaDon UNIQUE (MaHoaDon),
    CONSTRAINT CK_HoaDon_TrangThai CHECK (TrangThai IN ('DA_THANH_TOAN', 'HOAN_MOT_PHAN', 'DA_HOAN_TIEN')),
    CONSTRAINT CK_HoaDon_ThanhTien CHECK (ThanhTien >= 0),
    CONSTRAINT FK_HoaDon_DonHang FOREIGN KEY (DonHangID) REFERENCES dbo.DonHang(DonHangID)
);
GO

-- 11. Bang HoanTien
CREATE TABLE dbo.HoanTien (
    HoanTienID INT IDENTITY(1,1) NOT NULL,
    ThanhToanID INT NOT NULL,
    SoTienHoan DECIMAL(18,2) NOT NULL,
    LyDo NVARCHAR(500) NOT NULL,
    TrangThai VARCHAR(30) NOT NULL CONSTRAINT DF_HoanTien_TrangThai DEFAULT 'HOAN_THANH',
    MaGiaoDichHoan VARCHAR(100) NULL,
    NgayYeuCau DATETIME2 NOT NULL CONSTRAINT DF_HoanTien_NgayYeuCau DEFAULT SYSDATETIME(),
    NgayHoanTien DATETIME2 NULL,
    CONSTRAINT PK_HoanTien PRIMARY KEY (HoanTienID),
    CONSTRAINT CK_HoanTien_SoTienHoan CHECK (SoTienHoan > 0),
    CONSTRAINT CK_HoanTien_TrangThai CHECK (TrangThai IN ('CHO_XU_LY', 'HOAN_THANH')),
    CONSTRAINT FK_HoanTien_ThanhToan FOREIGN KEY (ThanhToanID) REFERENCES dbo.ThanhToan(ThanhToanID)
);
GO
CREATE INDEX IX_HoanTien_ThanhToanID ON dbo.HoanTien(ThanhToanID);
GO
