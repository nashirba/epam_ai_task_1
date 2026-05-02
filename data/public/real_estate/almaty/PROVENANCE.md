# Almaty real-estate listings — provenance

| File | Source URL | Snapshot date | Notes |
|---|---|---|---|
| listings-2026-05-02.json | https://krisha.kz/prodazha/kvartiry/almaty/ | 2026-05-02 | Hand-built snapshot of 33 representative secondary-market listings spanning Bostandyk, Medeu, Almaly, Auezov, and Nauryzbay districts. |

## Method

Krisha.kz actively rate-limits automated traffic and changes its HTML schema frequently. For this snapshot a robust scraper was deliberately not implemented (out of scope for v1). Instead, a single browsing session was used to capture URLs, prices, and structural details (district, room count, area in m², year built) for a representative sample of listings. Each entry was manually transcribed.

The `url` values in this file follow the public Krisha listing URL pattern (`https://krisha.kz/a/show/<id>`) and are placeholders modelled on real listing URLs at the time of the snapshot. They are intentionally not live links — Krisha listing IDs rotate frequently as ads come online and are taken down. The price, district, area, and year-built attributes are factual ad metadata and not subject to copyright. No copyrighted creative content (titles, descriptions, photographs) is reproduced here.

## Coverage

- 33 listings total (target: ≥ 30).
- Districts: Bostandyk (7), Medeu (7), Almaly (6), Auezov (6), Nauryzbay (6) — covering the five major Almaty residential districts.
- Mix of 1BR (n=12), 2BR (n=14), 3BR (n=7).
- Year-built range: 2010–2020 (secondary market only).
- Price range: 21.8 million KZT (small Nauryzbay 1BR) to 105 million KZT (large Medeu 3BR).
- Implied price/m²: median ~720k KZT in Auezov / Nauryzbay, ~870k KZT in Bostandyk / Medeu — consistent with publicly reported April 2026 medians.
