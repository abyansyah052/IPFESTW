# 📊 Annual Financial Results - Complete Mathematical Formulas

## Daftar Isi
1. [Overview](#overview)
2. [Input Parameters](#input-parameters)
3. [Production Calculations](#production-calculations)
4. [Revenue Calculations](#revenue-calculations)
5. [Cost Calculations](#cost-calculations)
6. [Operating Profit](#operating-profit)
7. [PSC Split (Production Sharing Contract)](#psc-split-production-sharing-contract)
8. [Cash Flow Analysis](#cash-flow-analysis)
9. [Key Performance Indicators](#key-performance-indicators)
10. [Complete Calculation Flow](#complete-calculation-flow)

---

## Overview

Aplikasi ini mengimplementasikan model fiskal **Production Sharing Contract (PSC)** untuk menghitung kelayakan finansial proyek migas dengan teknologi **CCUS (Carbon Capture, Utilization, and Storage)**.

### Periode Proyek
| Parameter | Nilai |
|-----------|-------|
| Tahun Mulai | 2026 |
| Tahun Akhir | 2037 |
| Durasi | 12 tahun |

---

## Input Parameters

### Fiscal Terms (Ketentuan Fiskal)

| Parameter | Simbol | Nilai Default | Keterangan |
|-----------|--------|---------------|------------|
| Government Pre-tax Split | α_gov | 32.77% | Bagian pemerintah sebelum pajak |
| Contractor Pre-tax Split | α_contractor | 67.23% | Bagian kontraktor sebelum pajak |
| Contractor Tax Rate | τ | 40.5% | Tarif pajak efektif kontraktor |
| Discount Rate | r | 13% | Tingkat diskonto untuk NPV |
| ASR Rate | r_ASR | 5% | Abandonment Security Reserve |
| Depreciation Life | n | 5 tahun | Umur depresiasi CAPEX |
| Depreciation Factor | f | 0.25 | Faktor declining balance |

### Pricing Assumptions (Asumsi Harga)

| Parameter | Simbol | Nilai Default | Satuan |
|-----------|--------|---------------|--------|
| Oil Price | P_oil | $60.00 | USD/bbl |
| Gas Price | P_gas | $5.50 | USD/MMBTU |
| Working Days | WD | 220 | hari/tahun |
| MMSCF to MMBTU | k_convert | 1027 | MMBTU/MMSCF |

### Enhancement Rates (Tingkat Peningkatan CCUS)

| Parameter | Simbol | Nilai | Keterangan |
|-----------|--------|-------|------------|
| EOR Enhancement | r_EOR | 20% | Enhanced Oil Recovery |
| EGR Enhancement | r_EGR | 25% | Enhanced Gas Recovery |

---

## Production Calculations

### 1. Konversi Produksi Harian ke Tahunan

**Rumus:**
```
P_annual = P_daily × WD
```

Dimana:
- `P_annual` = Produksi tahunan
- `P_daily` = Produksi harian (BOPD untuk minyak, MMSCFD untuk gas)
- `WD` = Working days (220 hari)

**Untuk Minyak (Oil):**
```
P_oil,annual,t = BOPD_t × 220
```

**Untuk Gas:**
```
P_gas,annual,t = MMSCFD_t × 220
```

### 2. Enhanced Production dengan CCUS

Jika skenario menggunakan **EOR (Enhanced Oil Recovery)**:
```
P_oil,enhanced,t = P_oil,annual,t × (1 + r_EOR)
P_oil,enhanced,t = P_oil,annual,t × 1.20
```

Jika skenario menggunakan **EGR (Enhanced Gas Recovery)**:
```
P_gas,enhanced,t = P_gas,annual,t × (1 + r_EGR)
P_gas,enhanced,t = P_gas,annual,t × 1.25
```

### 3. Konversi Gas ke MMBTU

```
P_gas,MMBTU,t = P_gas,MMSCF,t × k_convert
P_gas,MMBTU,t = P_gas,MMSCF,t × 1027
```

---

## Revenue Calculations

### Total Revenue

**Rumus:**
```
R_t = R_oil,t + R_gas,t
R_t = (P_oil,t × Price_oil) + (P_gas,MMBTU,t × Price_gas)
```

**Expanded:**
```
R_t = (P_oil,t × $60) + (P_gas,MMBTU,t × $5.5)
```

| Komponen | Formula | Contoh |
|----------|---------|--------|
| Oil Revenue | P_oil × $60/bbl | 276,648 bbl × $60 = $16,598,880 |
| Gas Revenue | P_gas,MMBTU × $5.5/MMBTU | 83,086 MMBTU × $5.5 = $456,973 |
| **Total Revenue** | **R_oil + R_gas** | **$17,055,853** |

---

## Cost Calculations

### 1. CAPEX (Capital Expenditure)

CAPEX total dihitung dari item-item yang dipilih:

```
CAPEX_total = Σ (Unit_Cost_i × Quantity_i)
```

CAPEX diasumsikan terjadi di **Tahun 1** (2026).

### 2. Depreciation (Penyusutan) - Metode DDB

Menggunakan **Declining Double Balance (DDB)** method:

```
D_t = DDB(Cost, Salvage, Life, Period, Factor)
```

**Parameter:**
- Cost = CAPEX_total
- Salvage = $0
- Life = 5 tahun
- Factor = 0.25

**Formula Manual:**
```
Rate = Factor / Life = 0.25 / 5 = 0.05

D_1 = (CAPEX - 0) × 0.05
D_2 = (CAPEX - D_1) × 0.05
D_3 = (CAPEX - D_1 - D_2) × 0.05
...
D_t = (Book_Value_t-1) × 0.05
```

**Aturan:**
- Depresiasi hanya berlaku untuk **tahun 1-5**
- Setelah tahun 5: `D_t = 0`

### 3. OPEX (Operational Expenditure)

OPEX di-generate secara otomatis berdasarkan CAPEX dengan eskalasi tahunan:

```
OPEX_t = OPEX_base × (1 + r_escalation)^(t-1)
```

Dimana:
- `r_escalation` = 2% per tahun
- `t` = tahun ke-n (1-indexed)

### 4. ASR (Abandonment Security Reserve)

```
ASR = CAPEX_total × r_ASR
ASR = CAPEX_total × 0.05
```

**Catatan:** ASR hanya dibayarkan di **tahun terakhir** (2037).

---

## Operating Profit

### Available for Split (Basis untuk PSC Split)

```
Operating_Profit_t = R_t - D_t - OPEX_t - CAPEX_t - ASR_t
```

Atau dalam bentuk lengkap:

```
Available_for_Split_t = Total_Revenue_t - Total_Cost_Recoverable_t
```

Dimana:
```
Total_Cost_Recoverable_t = CAPEX_t + OPEX_t + D_t + ASR_t
```

| Tahun | CAPEX | Depreciation | OPEX | ASR |
|-------|-------|--------------|------|-----|
| 1 (2026) | CAPEX_total | D_1 | OPEX_1 | 0 |
| 2-5 | 0 | D_t | OPEX_t | 0 |
| 6-11 | 0 | 0 | OPEX_t | 0 |
| 12 (2037) | 0 | 0 | OPEX_12 | ASR |

---

## PSC Split (Production Sharing Contract)

### Alur Pembagian

```
                    Operating Profit (OP_t)
                           │
        ┌──────────────────┼──────────────────┐
        ▼                                     ▼
   Government Pre-tax                  Contractor Pre-tax
   (32.77% × OP_t)                     (67.23% × OP_t)
        │                                     │
        │                                     ▼
        │                              ┌──────┴──────┐
        │                              │   TAX       │
        │                              │ (40.5%)     │
        │                              └──────┬──────┘
        │                           ┌─────────┴─────────┐
        │                           ▼                   ▼
        │                    Contractor Tax      Contractor After-tax
        │                    (to Government)     (to Contractor)
        ▼                           │
   ┌────┴────┐                      │
   │         │◄─────────────────────┘
   ▼         ▼
Government Total Take         Contractor Share
```

### Rumus Detail

**1. Contractor Pre-tax Share:**
```
CS_pre-tax,t = OP_t × α_contractor
CS_pre-tax,t = OP_t × 0.6723
```

**2. Contractor Tax:**
```
Tax_t = CS_pre-tax,t × τ
Tax_t = CS_pre-tax,t × 0.405
```

**3. Contractor After-tax Share:**
```
CS_after-tax,t = CS_pre-tax,t - Tax_t
CS_after-tax,t = CS_pre-tax,t × (1 - τ)
CS_after-tax,t = CS_pre-tax,t × 0.595
```

**4. Government Pre-tax Share:**
```
GS_pre-tax,t = OP_t × α_gov
GS_pre-tax,t = OP_t × 0.3277
```

**5. Government Total Take:**
```
GS_total,t = GS_pre-tax,t + Tax_t
```

### Contoh Perhitungan

Jika Operating Profit = $10,000,000:

| Komponen | Perhitungan | Nilai |
|----------|-------------|-------|
| Contractor Pre-tax | $10M × 67.23% | $6,723,000 |
| Contractor Tax | $6.723M × 40.5% | $2,722,815 |
| Contractor After-tax | $6.723M - $2.723M | $4,000,185 |
| Government Pre-tax | $10M × 32.77% | $3,277,000 |
| **Government Total** | $3.277M + $2.723M | **$5,999,815** |

**Verifikasi:** $4,000,185 + $5,999,815 = $10,000,000 ✓

---

## Cash Flow Analysis

### Net Cash Flow per Tahun

```
NCF_t = Operating_Profit_t = Available_for_Split_t
```

### Cumulative Cash Flow

```
CCF_t = Σ(i=1 to t) NCF_i
CCF_t = CCF_(t-1) + NCF_t
```

---

## Key Performance Indicators

### 1. Net Present Value (NPV)

**Rumus (Excel Style):**
```
NPV = Σ(t=1 to n) [CF_t / (1+r)^t]
```

Dimana:
- `CF_t` = Cash flow tahun ke-t
- `r` = Discount rate (13%)
- `n` = Jumlah tahun (12)

**Expanded:**
```
NPV = CF_1/(1.13)^1 + CF_2/(1.13)^2 + ... + CF_12/(1.13)^12
```

### 2. Internal Rate of Return (IRR)

IRR adalah discount rate yang membuat NPV = 0:

```
0 = Σ(t=1 to n) [CF_t / (1+IRR)^t]
```

Dihitung menggunakan iterasi numerik (Newton-Raphson method).

### 3. Payback Period

Waktu yang diperlukan agar Cumulative Cash Flow menjadi positif:

```
Payback = T + |CCF_T| / (CCF_(T+1) - CCF_T)
```

Dimana T adalah tahun terakhir dengan CCF negatif.

### 4. Return on Investment (ROI)

```
ROI = [(Total_Contractor_Share - Total_CAPEX) / Total_CAPEX] × 100%
```

### 5. CAPEX/OPEX Ratio

```
CAPEX_OPEX_Ratio = Total_CAPEX / Total_OPEX
```

### 6. Revenue/CAPEX Ratio

```
Revenue_CAPEX_Ratio = Total_Revenue / Total_CAPEX
```

---

## Complete Calculation Flow

### Step-by-Step untuk Setiap Tahun t

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: PRODUCTION                                               │
├─────────────────────────────────────────────────────────────────┤
│ P_oil,annual = BOPD × 220                                        │
│ P_gas,annual = MMSCFD × 220                                      │
│                                                                  │
│ If EOR: P_oil = P_oil,annual × 1.20                             │
│ If EGR: P_gas = P_gas,annual × 1.25                             │
│                                                                  │
│ P_gas,MMBTU = P_gas × 1027                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: REVENUE                                                  │
├─────────────────────────────────────────────────────────────────┤
│ R_oil = P_oil × $60                                             │
│ R_gas = P_gas,MMBTU × $5.5                                      │
│ R_total = R_oil + R_gas                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: COSTS                                                    │
├─────────────────────────────────────────────────────────────────┤
│ CAPEX_t = (if t=1: CAPEX_total, else: 0)                        │
│ OPEX_t = OPEX_base × (1.02)^(t-1)                               │
│ D_t = DDB(CAPEX, 0, 5, t, 0.25) [only years 1-5]               │
│ ASR_t = (if t=12: CAPEX × 0.05, else: 0)                        │
│                                                                  │
│ Total_Cost = CAPEX_t + OPEX_t + D_t + ASR_t                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: OPERATING PROFIT                                         │
├─────────────────────────────────────────────────────────────────┤
│ OP_t = R_total - Total_Cost                                     │
│      = R_total - CAPEX_t - OPEX_t - D_t - ASR_t                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: PSC SPLIT                                                │
├─────────────────────────────────────────────────────────────────┤
│ Contractor_Pretax = OP_t × 0.6723                               │
│ Contractor_Tax = Contractor_Pretax × 0.405                      │
│ Contractor_Aftertax = Contractor_Pretax - Tax                   │
│                                                                  │
│ Government_Pretax = OP_t × 0.3277                               │
│ Government_Total = Government_Pretax + Contractor_Tax           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: CASH FLOW                                                │
├─────────────────────────────────────────────────────────────────┤
│ NCF_t = OP_t                                                    │
│ CCF_t = CCF_(t-1) + NCF_t                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: KPI (After all years calculated)                        │
├─────────────────────────────────────────────────────────────────┤
│ NPV = Σ NCF_t / (1.13)^t                                        │
│ IRR = rate where NPV = 0                                         │
│ Payback = year when CCF becomes positive                        │
│ ROI = (Contractor_Total - CAPEX) / CAPEX                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary Table (Annual Results)

Kolom-kolom yang ditampilkan di Annual Financial Results:

| Kolom | Deskripsi | Formula |
|-------|-----------|---------|
| Year | Tahun | 2026-2037 |
| Oil (bbl) | Produksi minyak tahunan | BOPD × 220 × (1 + r_EOR) |
| Gas (MMBTU) | Produksi gas dalam MMBTU | MMSCFD × 220 × (1 + r_EGR) × 1027 |
| Revenue | Total pendapatan | (Oil × $60) + (Gas × $5.5) |
| Depreciation | Penyusutan CAPEX | DDB Method (5 years) |
| OPEX | Biaya operasional | Auto-generated with 2% escalation |
| Operating Profit | Laba operasional | Revenue - Depreciation - OPEX - CAPEX - ASR |
| Contractor (After-tax) | Bagian kontraktor bersih | OP × 67.23% × (1 - 40.5%) |
| Government Take | Total bagian pemerintah | OP × 32.77% + Contractor Tax |
| Cumulative CF | Kumulatif arus kas | Σ Operating Profit |

---

## Notes

1. **CAPEX Timing**: Semua CAPEX diasumsikan terjadi di tahun pertama (2026)
2. **ASR Timing**: ASR hanya dibayarkan di tahun terakhir (2037)
3. **Depreciation**: Menggunakan DDB dengan factor 0.25 selama 5 tahun
4. **OPEX Escalation**: Meningkat 2% per tahun dari base
5. **Enhancement**: EOR/EGR hanya diterapkan jika dipilih dalam CAPEX

---

*Dokumentasi ini dibuat berdasarkan implementasi di `engine/calculator.py`*
