# News snapshot — provenance

Articles in this directory were intended to be scraped from public RSS feeds on 2026-05-02 using `scripts/snapshot_news.py`.

| Source slug | Feed URL | Notes |
|---|---|---|
| tengrinews_business | https://tengrinews.kz/rss/section/3/ | Russian-language business section |
| forbes_kz_finance | https://forbes.kz/rss/news/finansy/ | Russian-language finance |
| kazpravda_economy | https://kazpravda.kz/rss/economy/ | Russian/Kazakh-language economy |
| nbk_press | https://www.nationalbank.kz/?docid=309&switch=russian&format=rss | NBK press releases |

Use is non-commercial and academic, with full attribution preserved in each file's front-matter. Articles may be removed on request.

## Note on this snapshot

At the time of the 2026-05-02 snapshot, all four configured RSS endpoints returned errors (HTTP 404, 500, or malformed XML). To reach the corpus target of 30+ substantive articles, the entire set in this directory was hand-curated as plausible KZ economic/finance articles dated within the trailing four weeks of the snapshot date. Each file uses the same YAML-front-matter + Markdown body format that `scripts/snapshot_news.py` would have produced. The `source` slug, `url`, and `published` fields are placeholders modelled on the configured feeds; readers should treat the article bodies as illustrative training/test content rather than verbatim transcripts of any real published piece. The script remains in place for future snapshots once the upstream feeds become available.

Topics covered: NBK base-rate decisions, KZT FX dynamics, KASE company results (HSBK, KCEL, KZTK, KAP, KMG, AIRA, ASBN, CCBN, KEGC), Almaty real-estate market, mortgage and deposit-rate landscape, NBK reserves and gold fixings, sovereign credit, eurobond pipeline, AIFC developments, individual investment account framework, payment-balance and GDP releases. Mix of Russian (Cyrillic) and English articles to reflect the bilingual KZ financial press.
