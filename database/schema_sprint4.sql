-- =====================================================
-- Schema Sprint 4: Khuyen mai, nhan vien, ca lam viec, lich lam viec
-- Chay SAU schema.sql, schema_sprint2.sql, schema_sprint3.sql.
-- Chay lai nhieu lan an toan: bang da co thi bo qua (KHONG xoa du lieu).
-- Quy tac: PK_, FK_, UQ_, CK_, DF_ | PK INT IDENTITY | DECIMAL cho tien
--
-- KhuyenMai.LoaiGiamGia: PHAN_TRAM (GiaTriGiam 0-100, co the gioi han GiamToiDa) | SO_TIEN
-- Moi don ap dung toi da 1 khuyen mai (UQ_SuDungKhuyenMai_DonHangID).
-- NhanVien.TrangThai: DANG_LAM | TAM_NGHI | NGHI_VIEC
-- LichLamViec.TrangThai: DA_XEP | DA_LAM | VANG | DA_HUY
-- =====================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- 18. Bang KhuyenMai
IF OBJECT_ID('dbo.KhuyenMai', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.KhuyenMai (
        KhuyenMaiID INT IDENTITY(1,1) NOT NULL,
        MaKhuyenMai VARCHAR(50) NOT NULL,
        TenKhuyenMai NVARCHAR(150) NOT NULL,
        LoaiGiamGia VARCHAR(20) NOT NULL,
        GiaTriGiam DECIMAL(18,2) NOT NULL,
        DonHangToiThieu DECIMAL(18,2) NOT NULL CONSTRAINT DF_KhuyenMai_DonHangToiThieu DEFAULT 0,
        GiamToiDa DECIMAL(18,2) NULL,
        SoLuongSuDung INT NULL,
        NgayBatDau DATETIME2 NOT NULL,
        NgayKetThuc DATETIME2 NOT NULL,
        TrangThai BIT NOT NULL CONSTRAINT DF_KhuyenMai_TrangThai DEFAULT 1,
        NgayTao DATETIME2 NOT NULL CONSTRAINT DF_KhuyenMai_NgayTao DEFAULT SYSDATETIME(),
        NgayCapNhat DATETIME2 NULL,
        CONSTRAINT PK_KhuyenMai PRIMARY KEY (KhuyenMaiID),
        CONSTRAINT UQ_KhuyenMai_MaKhuyenMai UNIQUE (MaKhuyenMai),
        CONSTRAINT CK_KhuyenMai_LoaiGiamGia CHECK (LoaiGiamGia IN ('PHAN_TRAM', 'SO_TIEN')),
        CONSTRAINT CK_KhuyenMai_GiaTriGiam CHECK (
            GiaTriGiam > 0 AND (LoaiGiamGia <> 'PHAN_TRAM' OR GiaTriGiam <= 100)),
        CONSTRAINT CK_KhuyenMai_DonHangToiThieu CHECK (DonHangToiThieu >= 0),
        CONSTRAINT CK_KhuyenMai_GiamToiDa CHECK (GiamToiDa IS NULL OR GiamToiDa > 0),
        CONSTRAINT CK_KhuyenMai_SoLuongSuDung CHECK (SoLuongSuDung IS NULL OR SoLuongSuDung > 0),
        CONSTRAINT CK_KhuyenMai_Ngay CHECK (NgayKetThuc > NgayBatDau)
    );
    CREATE INDEX IX_KhuyenMai_Ngay ON dbo.KhuyenMai(NgayBatDau, NgayKetThuc);
END
GO

-- 19. Bang SuDungKhuyenMai (khuyen mai ap vao don nao, giam bao nhieu)
IF OBJECT_ID('dbo.SuDungKhuyenMai', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.SuDungKhuyenMai (
        SuDungKhuyenMaiID INT IDENTITY(1,1) NOT NULL,
        KhuyenMaiID INT NOT NULL,
        DonHangID INT NOT NULL,
        SoTienGiam DECIMAL(18,2) NOT NULL,
        NgaySuDung DATETIME2 NOT NULL CONSTRAINT DF_SuDungKhuyenMai_NgaySuDung DEFAULT SYSDATETIME(),
        CONSTRAINT PK_SuDungKhuyenMai PRIMARY KEY (SuDungKhuyenMaiID),
        CONSTRAINT UQ_SuDungKhuyenMai_DonHangID UNIQUE (DonHangID),
        CONSTRAINT CK_SuDungKhuyenMai_SoTienGiam CHECK (SoTienGiam >= 0),
        CONSTRAINT FK_SuDungKhuyenMai_KhuyenMai FOREIGN KEY (KhuyenMaiID) REFERENCES dbo.KhuyenMai(KhuyenMaiID),
        CONSTRAINT FK_SuDungKhuyenMai_DonHang FOREIGN KEY (DonHangID) REFERENCES dbo.DonHang(DonHangID)
    );
    CREATE INDEX IX_SuDungKhuyenMai_KhuyenMaiID ON dbo.SuDungKhuyenMai(KhuyenMaiID);
END
GO

-- 20. Bang NhanVien (ho so nhan su, co the gan 1 tai khoan dang nhap)
IF OBJECT_ID('dbo.NhanVien', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.NhanVien (
        NhanVienID INT IDENTITY(1,1) NOT NULL,
        TaiKhoanID INT NULL,
        MaNhanVien VARCHAR(30) NOT NULL,
        HoTen NVARCHAR(100) NOT NULL,
        SoDienThoai VARCHAR(15) NULL,
        DiaChi NVARCHAR(255) NULL,
        ChucVu NVARCHAR(50) NULL,
        NgayVaoLam DATE NULL,
        TrangThai VARCHAR(20) NOT NULL CONSTRAINT DF_NhanVien_TrangThai DEFAULT 'DANG_LAM',
        NgayTao DATETIME2 NOT NULL CONSTRAINT DF_NhanVien_NgayTao DEFAULT SYSDATETIME(),
        NgayCapNhat DATETIME2 NULL,
        CONSTRAINT PK_NhanVien PRIMARY KEY (NhanVienID),
        CONSTRAINT UQ_NhanVien_MaNhanVien UNIQUE (MaNhanVien),
        CONSTRAINT CK_NhanVien_TrangThai CHECK (TrangThai IN ('DANG_LAM', 'TAM_NGHI', 'NGHI_VIEC')),
        CONSTRAINT FK_NhanVien_TaiKhoan FOREIGN KEY (TaiKhoanID) REFERENCES dbo.TaiKhoan(TaiKhoanID)
    );
    -- UNIQUE nhung cho phep nhieu ho so chua gan tai khoan.
    CREATE UNIQUE INDEX UQ_NhanVien_TaiKhoanID ON dbo.NhanVien(TaiKhoanID) WHERE TaiKhoanID IS NOT NULL;
END
GO

-- 21. Bang CaLamViec
IF OBJECT_ID('dbo.CaLamViec', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CaLamViec (
        CaLamViecID INT IDENTITY(1,1) NOT NULL,
        TenCa NVARCHAR(50) NOT NULL,
        GioBatDau TIME(0) NOT NULL,
        GioKetThuc TIME(0) NOT NULL,
        MoTa NVARCHAR(255) NULL,
        TrangThai BIT NOT NULL CONSTRAINT DF_CaLamViec_TrangThai DEFAULT 1,
        CONSTRAINT PK_CaLamViec PRIMARY KEY (CaLamViecID),
        CONSTRAINT UQ_CaLamViec_TenCa UNIQUE (TenCa),
        -- Ca qua dem (vd 22:00-06:00) cho phep, chi cam gio bat dau = gio ket thuc.
        CONSTRAINT CK_CaLamViec_Gio CHECK (GioBatDau <> GioKetThuc)
    );
END
GO

-- 22. Bang LichLamViec (phan cong nhan vien vao ca theo ngay)
IF OBJECT_ID('dbo.LichLamViec', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.LichLamViec (
        LichLamViecID INT IDENTITY(1,1) NOT NULL,
        NhanVienID INT NOT NULL,
        CaLamViecID INT NOT NULL,
        NgayLam DATE NOT NULL,
        TrangThai VARCHAR(20) NOT NULL CONSTRAINT DF_LichLamViec_TrangThai DEFAULT 'DA_XEP',
        GhiChu NVARCHAR(255) NULL,
        NgayTao DATETIME2 NOT NULL CONSTRAINT DF_LichLamViec_NgayTao DEFAULT SYSDATETIME(),
        NgayCapNhat DATETIME2 NULL,
        CONSTRAINT PK_LichLamViec PRIMARY KEY (LichLamViecID),
        CONSTRAINT CK_LichLamViec_TrangThai CHECK (TrangThai IN ('DA_XEP', 'DA_LAM', 'VANG', 'DA_HUY')),
        CONSTRAINT FK_LichLamViec_NhanVien FOREIGN KEY (NhanVienID) REFERENCES dbo.NhanVien(NhanVienID),
        CONSTRAINT FK_LichLamViec_CaLamViec FOREIGN KEY (CaLamViecID) REFERENCES dbo.CaLamViec(CaLamViecID)
    );
    -- Mot nhan vien khong bi xep trung cung ca cung ngay (lich da huy thi duoc xep lai).
    CREATE UNIQUE INDEX UQ_LichLamViec_NV_Ca_Ngay ON dbo.LichLamViec(NhanVienID, CaLamViecID, NgayLam)
        WHERE TrangThai <> 'DA_HUY';
    CREATE INDEX IX_LichLamViec_NgayLam ON dbo.LichLamViec(NgayLam);
END
GO
