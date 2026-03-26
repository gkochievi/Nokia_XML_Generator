# Nokia XML Generator - Improvement Roadmap

## Goal
Make XML modernization/rollout safer, faster, and easier for daily use by reducing manual checks, improving validation, and adding automation.

## How To Read This
- **High Priority**: biggest impact on correctness and time savings.
- **Medium Priority**: improves usability and scalability.
- **Nice to Have**: valuable, but can wait until core workflow is stable.

---

## High Priority (Do First)

### 1) Strong XML Validation
**Why**: Prevent bad outputs before they reach production.

- Add **pre-generation validation** for uploaded existing/reference XML (Nokia RAML structure checks).
- Add **post-generation validation** to verify required objects/parameters exist.
- Add **replacement completeness checks** and warnings for critical fields:
  - PCI
  - TAC
  - IP/VLAN/Gateway

**Expected result**: fewer failed integrations and faster troubleshooting.

### 2) XML Diff / Comparison Page
**Why**: Users need to quickly verify what changed.

- New page to upload/select 2 XML files and see a visual diff.
- Highlight:
  - Added 5G managed objects
  - Changed IP/VLAN values
  - Name/ID replacements
- Group differences by object type and parameter.

**Expected result**: safer acceptance before download/deployment.

### 3) Batch Modernization
**Why**: Single-station generation does not scale.

- Upload station list from Excel and generate all outputs in one run.
- Queue-based processing with progress/status per station.
- Download all generated XML files as ZIP.

**Expected result**: major time savings for mass modernization.

### 4) Complete Missing Parameter Replacements
**Why**: Some replacement coverage is partial.

Expand replacement logic for:
- `configuredEpsTac` on 5G `NRCELL`
- `LNHOIF` IP parameters
- `NRHOIF` parameters
- `LNADJW` / `WNADJL` inter-RAT neighbor parameters
- `sctpPortMin` for S1/X2/XN
- `TAC` for `LNCEL_TDD` (already partly handled; make robust)

**Expected result**: more consistent outputs across different site variants.

### 5) Radio Parameters Excel Support
**Why**: Today, Excel support is mostly IP-plan focused.

- Add a second Excel import path for radio settings:
  - antenna tilt
  - TX power
  - MIMO mode
  - carrier configuration

**Expected result**: near end-to-end config generation from structured Excel inputs.

---

## Medium Priority

### 6) Template Library
- Save custom templates with notes.
- Version by release (`V25R1`, `V25R2`, `V25R3`).
- Tag by use case (macro/small cell/IoT/indoor).

### 7) Station Inventory Database
- Build inventory from BTS naming Excel + SFTP backups.
- Search/filter by region/technology.
- Launch modernization directly from station record.

### 8) Generated XML Preview Before Download
- Show key replacements before user downloads.
- Side-by-side reference vs generated snippets.
- Expand/collapse by replacement category.

### 9) Rollout Flow Improvements
- Auto-fill BTS ID from sequence/Excel.
- Multi-site rollout from spreadsheet.
- Template auto-selection based on site type.

### 10) Exported Reports
- Generate PDF/Excel report per generation.
- Include before/after parameter values.
- Add site-level summary for audit trail.

---

## Nice To Have

### 11) Real-Time SFTP Browser
- Browse remote backup folders from UI.
- Preview XML before download.
- Compare backup vs generated file.

### 12) Neighbor Plan Import
- Import neighbor plan Excel.
- Auto-update LNADJ/NRADJ/X2LINK objects.

### 13) Map View
- Plot stations (if coordinates exist).
- Start modernization directly from map.

### 14) User Accounts and History
- Multi-user authentication.
- Track who generated what and when.
- Add rollback/restore support.

### 15) API / External Integration
- REST endpoint for external trigger.
- Optional integration with NetAct/SAM workflows.

### 16) Theme Toggle
- Add dark/light switch.

### 17) Keyboard Shortcuts
- `Ctrl+G` generate
- `Ctrl+M` manage files
- `Ctrl+U` upload

---

## Suggested Implementation Phases

### Phase 1 (Stability)
1. XML validation
2. Missing replacement coverage
3. Generated preview

### Phase 2 (Productivity)
1. XML diff page
2. Batch modernization
3. Radio parameters Excel support

### Phase 3 (Scale / Platform)
1. Template library + station database
2. Reports + API integration
3. Optional enterprise features (accounts, map)

---

## Success Metrics

- **Error rate**: fewer failed/invalid generated XML files.
- **Time per station**: lower average generation + verification time.
- **Manual edits**: fewer post-generation manual fixes.
- **Batch throughput**: number of stations processed per run.
