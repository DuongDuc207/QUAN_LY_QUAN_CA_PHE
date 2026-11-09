-- Incremental database update 01: promotions and promotion usage.
-- Apply after schema.sql, schema_sprint2.sql, and schema_sprint3.sql.
-- Safe to re-run: existing tables are left unchanged.

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

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
