-- Allow a cashier to confirm a zero-total order (e.g. a 100% promotion).
-- Existing orders and payments are preserved. Safe to re-run.
SET XACT_ABORT ON;
GO
BEGIN TRANSACTION;
IF OBJECT_ID('dbo.CK_ThanhToan_SoTien', 'C') IS NOT NULL
    ALTER TABLE dbo.ThanhToan DROP CONSTRAINT CK_ThanhToan_SoTien;
ALTER TABLE dbo.ThanhToan WITH CHECK
    ADD CONSTRAINT CK_ThanhToan_SoTien CHECK (SoTien >= 0);
COMMIT TRANSACTION;
GO
