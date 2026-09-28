# 1f. Data sources for the next phase

Checked 2026-09-28. **No samples were downloaded for any of these sources**; the reason is given for each. File sizes come from HTTP HEAD responses (`Content-Length`).

| Source | URL | Format | Resolution | Licence | Download without login? | Sample |
|---|---|---|---|---|---|---|
| WorldPop India | hub.worldpop.org (REST API) | GeoTIFF | 100 m (also 1 km) | **CC BY 4.0** | **Yes** (direct HTTPS file) | No: national file only (775 MB – 1.84 GB) and no raster library installed |
| GSI landslide susceptibility (Bhukosh) | bhukosh.gsi.gov.in | COULD NOT VERIFY (portal unreachable) | 1:50,000 (NLSM) | COULD NOT VERIFY | COULD NOT VERIFY | No: portal unreachable |
| ↳ same GSI 2022 maps, hosted by KSDMA | sdma.kerala.gov.in/hazard-maps/ | "Shape files" (zip); Wayanad.zip = 3,072,545 bytes | COULD NOT VERIFY (NLSM is 1:50,000) | Site footer: "All rights reserved"; no open licence found | **Yes** (public link, HTTP 200) | No: no open licence |
| KSDMA flood hazard probability | sdma.kerala.gov.in/hazard-maps/ | "Raster File Zip" (4.4–4.8 MB) and district PDFs | "about 1.4 km and rescalled to 90 m" | "All rights reserved" | **Yes** (public link, HTTP 200) | No: no open licence |
| NRSC / Bhuvan 2018 Kerala flood inundation | ndem.nrsc.gov.in; bhuvan-app1.nrsc.gov.in | Official GIS layer: COULD NOT VERIFY; PDF map and report are public | COULD NOT VERIFY (Radarsat-2 SAR source) | COULD NOT VERIFY (official) | Report PDF yes; NDEM portal restricted (see 1a) | No |
| ↳ community mirror of NDEM layers | github.com/ramSeraph/india_natural_disasters (release "floods") | geojsonl.7z / parquet / pmtiles | "(at 1:250k resolution?)" (the mirror's own question mark) | Mirror claims "CC0 1.0 but attribute … the original government source" | Yes | No: 32 MB, upstream licence unverified, and whether it includes 2018 is unverified |
| IMD gridded rainfall | imdpune.gov.in/cmpg/Griddata/ | Binary (.grd) or NetCDF | 0.25° × 0.25°, daily, 1901–2024 | No licence text; citation requested (Pai et al. 2014) | **Yes, apparently**: POST form, no login field seen | No: no explicit licence; each file is national, one year |

---

## WorldPop (population raster, India)
- **API:** https://hub.worldpop.org/rest/data/pop/wpgp?iso3=IND (21 entries, 2000–2020) and https://hub.worldpop.org/rest/data/pop/G2_CN_POP_R25A_100m?iso3=IND (16 entries).
- **Excerpts (API JSON):**
  - Legacy: `"title": "The spatial distribution of population in 2020, India"`, `"doi": "10.5258/SOTON/WP00645"`, `"data_format": "Geotiff"`, `"files": ["https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/IND/ind_ppp_2020.tif"]`.
  - Newer release: `"title": "India - Spatial Distribution of Population"`, `"doi": "10.5258/SOTON/WP00839"`, `"date": "2025-09-01"`, `"popyear": "2024"`, `"files": [".../R2025A/2024/IND/v1/100m/constrained/ind_pop_2024_CN_100m_R2025A_v1.tif"]`.
- **Dataset list (API):** "Unconstrained individual countries 2000-2020 ( 100m resolution )", "Individual countries 2015-2030 ( 100m resolution ) R2025A v1", "Individual countries 2015-2030 ( 1km resolution ) R2025A v1", among others.
- **Licence (https://hub.worldpop.org/data/licence.txt):** "WorldPop datasets are licensed under the Creative Commons Attribution 4.0 International License".
- **Sizes (HEAD):** ind_ppp_2020.tif, Content-Length 1,844,139,160; ind_pop_2024_CN_100m_R2025A_v1.tif, Content-Length 774,952,521. No login was needed for the HEAD request.
- **Sample:** not taken. There's no Kerala-only file, and `rasterio` isn't installed, so I couldn't read a window over HTTP. I didn't install it.

## GSI landslide susceptibility (Bhukosh)
- **https://bhukosh.gsi.gov.in/Bhukosh/Public:** COULD NOT OPEN. Local attempt: connect timeout after 40 s (3 tries). WebFetch: `ECONNREFUSED 144.24.99.164:443`.
- **MoES document (https://www.moes.gov.in/static/uploads/2025/08/d4aabb5c7a226df21f4b5b40d40d432d.pdf), excerpts:** "susceptibility mapping under the National Landslide Susceptibility Mapping (NLSM) programme on 1: 50,000". "The landslide susceptibility map and the landslide inventory generated are uploaded in the GSI's National Geoscience Data Repository (NGDR) and Bhukosh map portal for free download by all the stakeholders." "GSI has upscaled into meso-scale (1:10,000/1:5,000) landslide susceptibility".
- **GSI Bhusanket (https://bhusanket.gsi.gov.in/LS_hazard.html), excerpt:** "has been covered through landslide susceptibility mapping on 1:50,000 scale."
- **Login requirement, file format and licence on Bhukosh itself:** COULD NOT VERIFY.
- **Alternative route to the same data:** KSDMA hosts "Landslide Susceptibility zones of District of Kerala (GSI, 2022)- Shape files", with Wayanad at https://sdma.kerala.gov.in/wp-content/uploads/2025/08/Wayanad.zip (HEAD: 200 OK, application/zip, 3,072,545 bytes, Last-Modified 21 Aug 2025). KSDMA's note (excerpt): "As Geological Survey of India (GSI), the National Nodal Agency for Landslide Hazard Susceptibility Mapping has published the landslide susceptibility map of Kerala, the LSM of GSI will replace all other maps used in any document published by KSDMA."

## KSDMA hazard layers
- **Pages:** https://sdma.kerala.gov.in/hazard-maps/ and https://sdma.kerala.gov.in/maps/
- **Items listed (verbatim):**
  - "Flood Hazard Probability (based on Historic Data) Maps and Exposure of Schools and Hospitals in each district (PDFs)"
  - "Flood Hazard Probability of Kerala based on Historic Data (Raster File Zip) (Reference: UNEP, UN GRID, CIMA Italy, KSDMA, 2020; Flood Return Probability Assessment of Kerala & M/S RMSI and National Insurance Academy,2024)"
  - "Flood Return Probability (10, 25, 50 years)" and "(100, 200, 500 years)"
  - "Landslide Susceptibility zones of District of Kerala (GSI, 2022)- Shape files"
  - "List of Landslide Susceptible Villages of Kerala"
  - "Flood Susceptibility Zones of Districts of Kerala (NCESS, 2010) – File uploaded in KML format for use in Google Earth Pro."
- **Sizes (HEAD, all 200 OK):**
  - Historical 10/25/50-yr zip: 4,370,593 bytes (Last-Modified 6 Jun 2026)
  - Historical 100/200/500-yr zip: 4,753,860 bytes
  - Wayanad historical flood PDF: 10,485,308 bytes
- **Resolution (https://sdma.kerala.gov.in/wp-content/uploads/2022/06/Flood-Probability-Report-2022_Final.pdf), excerpt:** "The distributed model has implemented on the entire Kerala state with a spatial resolution of about 1.4 km and rescalled to 90 m."
- **Licence:** the page footer says "Copyright © 2026.KERALA STATE DISASTER MANAGEMENT AUTHORITY. All rights reserved." I found no open-data licence. **Inference:** the files are publicly linked with no login, but reusing them would need KSDMA's permission or a confirmed licence.

## NRSC / Bhuvan 2018 Kerala flood inundation
- **NDEM report (https://ndem.nrsc.gov.in/documents/Disaster_Document/2018/KL/klflood50dsc21082018/klflood50dsc21082018_report.pdf), excerpts:** "Date: August 21, 2018". "Sub: Kerala Floods 2018- Near Real Time Inundation Mapping using satellite data". "We have analyzed Radarsat-2 SAR data of 21st August". "In addition, the flood layer in GIS ready format and inundation statistics ar e transmitted to".
- **Inference:** the GIS-ready layer was sent to government recipients. Whether it's publicly downloadable from NDEM: COULD NOT VERIFY. The NDEM portal is restricted to authorised officials per the 2015 manual (see competitors.md).
- **Community mirror (https://github.com/ramSeraph/india_natural_disasters, release "floods"; repo last push 2025-02-22; no GitHub licence), release notes excerpt:** "NDEM All India aggregate flood Innundation 1998 to 2022 (at 1:250k resolution?)". "License: CC0 1.0 but attribute datameet and the original government source where possible". Kerala assets include `NDEM_KL_Floods_Inundation.geojsonl.7z` (31,948,811 bytes) and `NDEM_KL_Yearly_Aggregate_Flood_Innundation_2021.*`. **Whether the 2018 event is included: COULD NOT VERIFY** (not downloaded). The CC0 is the mirror's claim, not NRSC's.
- Bhuvan flood hazard page (https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php?id=flood_hz): **search snippet only**, not opened.

## IMD gridded rainfall
- **Pages:** https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html (binary) and https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html (NetCDF)
- **Excerpts:** "IMD New High Spatial Resolution (0.25X0.25 degree) Long Period (1901-2024) Daily Gridded Rainfall Data Set Over India." "Data is arranged in 135x129 grid points." "The yearly data file consists of 365/366 records corresponding to non leap/ leap years." "Should you refer to our product in your paper/presentation, please cite Pai et al. (2014)."
- **Download mechanism (raw HTML):** `<form class="form-inline" name="RF25" action="RF25.php" method="post">` with a year `<select>` and a "Download" button. There's no login or registration field on the page, so **it appears downloadable without a login**; I didn't submit the form.
- **Licence:** no licence text found; only the citation request.
- **Resolution note (inference):** 0.25° is about 27 km. Wayanad (about 2,130 km²) would be covered by only a few grid cells.
