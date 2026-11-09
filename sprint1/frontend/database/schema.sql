-- =====================================================
-- Schema Sprint 1: Tai khoan, phan quyen, danh muc, thuc don
-- DB: QuanLyCaPhe (SQL Server)
-- Quy tac: PK_, FK_, UQ_, CK_, DF_ | PK INT IDENTITY | DECIMAL cho tien
-- =====================================================

-- Xoa theo thu tu FK nguoc (Mon -> TaiKhoan -> VaiTroQuyen -> Quyen/VaiTro/DanhMuc)
IF OBJECT_ID('dbo.Mon', 'U') IS NOT NULL DROP TABLE dbo.Mon;
IF OBJECT_ID('dbo.TaiKhoan', 'U') IS NOT NULL DROP TABLE dbo.TaiKhoan;
IF OBJECT_ID('dbo.VaiTroQuyen', 'U') IS NOT NULL DROP TABLE dbo.VaiTroQuyen;
IF OBJECT_ID('dbo.Quyen', 'U') IS NOT NULL DROP TABLE dbo.Quyen;
IF OBJECT_ID('dbo.VaiTro', 'U') IS NOT NULL DROP TABLE dbo.VaiTro;
IF OBJECT_ID('dbo.DanhMuc', 'U') IS NOT NULL DROP TABLE dbo.DanhMuc;
GO

-- 1. Bang VaiTro
CREATE TABLE dbo.VaiTro (
    VaiTroID INT IDENTITY(1,1) NOT NULL,
    TenVaiTro NVARCHAR(50) NOT NULL,
    MoTa NVARCHAR(255) NULL,
    NgayTao DATETIME2 NOT NULL CONSTRAINT DF_VaiTro_NgayTao DEFAULT SYSDATETIME(),
    CONSTRAINT PK_VaiTro PRIMARY KEY (VaiTroID),
    CONSTRAINT UQ_VaiTro_TenVaiTro UNIQUE (TenVaiTro)
);
GO

-- 2. Bang Quyen
CREATE TABLE dbo.Quyen (
    QuyenID INT IDENTITY(1,1) NOT NULL,
    TenQuyen NVARCHAR(100) NOT NULL,
    MoTa NVARCHAR(255) NULL,
    CONSTRAINT PK_Quyen PRIMARY KEY (QuyenID),
    CONSTRAINT UQ_Quyen_TenQuyen UNIQUE (TenQuyen)
);
GO

-- 3. Bang VaiTroQuyen (nhieu-nhieu)
CREATE TABLE dbo.VaiTroQuyen (
    VaiTroID INT NOT NULL,
    QuyenID INT NOT NULL,
    CONSTRAINT PK_VaiTroQuyen PRIMARY KEY (VaiTroID, QuyenID),
    CONSTRAINT FK_VaiTroQuyen_VaiTro FOREIGN KEY (VaiTroID) REFERENCES dbo.VaiTro(VaiTroID),
    CONSTRAINT FK_VaiTroQuyen_Quyen FOREIGN KEY (QuyenID) REFERENCES dbo.Quyen(QuyenID)
);
GO

-- 4. Bang TaiKhoan
CREATE TABLE dbo.TaiKhoan (
    TaiKhoanID INT IDENTITY(1,1) NOT NULL,
    VaiTroID INT NOT NULL,
    HoTen NVARCHAR(100) NOT NULL,
    Email VARCHAR(255) NOT NULL,
    MatKhauHash VARCHAR(255) NOT NULL,
    SoDienThoai VARCHAR(15) NULL,
    TrangThai VARCHAR(20) NOT NULL CONSTRAINT DF_TaiKhoan_TrangThai DEFAULT 'HOAT_DONG',
    NgayTao DATETIME2 NOT NULL CONSTRAINT DF_TaiKhoan_NgayTao DEFAULT SYSDATETIME(),
    NgayCapNhat DATETIME2 NULL,
    CONSTRAINT PK_TaiKhoan PRIMARY KEY (TaiKhoanID),
    CONSTRAINT UQ_TaiKhoan_Email UNIQUE (Email),
    CONSTRAINT CK_TaiKhoan_TrangThai CHECK (TrangThai IN ('HOAT_DONG', 'KHOA')),
    CONSTRAINT FK_TaiKhoan_VaiTro FOREIGN KEY (VaiTroID) REFERENCES dbo.VaiTro(VaiTroID)
);
GO
CREATE INDEX IX_TaiKhoan_VaiTroID ON dbo.TaiKhoan(VaiTroID);
GO

-- 5. Bang DanhMuc
CREATE TABLE dbo.DanhMuc (
    DanhMucID INT IDENTITY(1,1) NOT NULL,
    TenDanhMuc NVARCHAR(100) NOT NULL,
    MoTa NVARCHAR(255) NULL,
    TrangThai BIT NOT NULL CONSTRAINT DF_DanhMuc_TrangThai DEFAULT 1,
    NgayTao DATETIME2 NOT NULL CONSTRAINT DF_DanhMuc_NgayTao DEFAULT SYSDATETIME(),
    CONSTRAINT PK_DanhMuc PRIMARY KEY (DanhMucID)
);
GO

-- 6. Bang Mon
CREATE TABLE dbo.Mon (
    MonID INT IDENTITY(1,1) NOT NULL,
    DanhMucID INT NOT NULL,
    TenMon NVARCHAR(150) NOT NULL,
    MoTa NVARCHAR(500) NULL,
    GiaBan DECIMAL(18,2) NOT NULL,
    HinhAnh NVARCHAR(500) NULL,
    TrangThai BIT NOT NULL CONSTRAINT DF_Mon_TrangThai DEFAULT 1,
    NgayTao DATETIME2 NOT NULL CONSTRAINT DF_Mon_NgayTao DEFAULT SYSDATETIME(),
    NgayCapNhat DATETIME2 NULL,
    CONSTRAINT PK_Mon PRIMARY KEY (MonID),
    CONSTRAINT CK_Mon_GiaBan CHECK (GiaBan >= 0),
    CONSTRAINT FK_Mon_DanhMuc FOREIGN KEY (DanhMucID) REFERENCES dbo.DanhMuc(DanhMucID)
);
GO
CREATE INDEX IX_Mon_DanhMucID ON dbo.Mon(DanhMucID);
GO
CREATE INDEX IX_Mon_TenMon ON dbo.Mon(TenMon);
GO
