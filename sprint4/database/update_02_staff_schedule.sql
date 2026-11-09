-- Incremental database update 02: employees, shifts, and work schedules.
-- Apply after schema.sql, schema_sprint2.sql, and schema_sprint3.sql.
-- Safe to re-run: existing tables are left unchanged.

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

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
    CREATE UNIQUE INDEX UQ_NhanVien_TaiKhoanID ON dbo.NhanVien(TaiKhoanID)
        WHERE TaiKhoanID IS NOT NULL;
END
GO

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
        CONSTRAINT CK_CaLamViec_Gio CHECK (GioBatDau <> GioKetThuc)
    );
END
GO

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
    CREATE UNIQUE INDEX UQ_LichLamViec_NV_Ca_Ngay ON dbo.LichLamViec(NhanVienID, CaLamViecID, NgayLam)
        WHERE TrangThai <> 'DA_HUY';
    CREATE INDEX IX_LichLamViec_NgayLam ON dbo.LichLamViec(NgayLam);
END
GO
