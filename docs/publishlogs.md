Run python publish.py --no-site --no-translate
[publish] wiping DB...
[publish] ingest...
09:07:18 INFO    grounded.ingest.google_news: [pib] fetching https://news.google.com/rss/search?q=site%3Apib.gov.in+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen
09:07:18 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=site%3Apib.gov.in+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
09:07:18 INFO    grounded.ingest.google_news: [supreme_court] fetching https://news.google.com/rss/search?q=site%3Asci.gov.in+OR+%22supreme+court+of+india%22+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen
09:07:19 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=site%3Asci.gov.in+OR+%22supreme+court+of+india%22+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
09:07:19 INFO    grounded.ingest.google_news: [rbi] fetching https://news.google.com/rss/search?q=site%3Arbi.org.in+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen
09:07:19 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=site%3Arbi.org.in+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
09:07:19 INFO    grounded.ingest.google_news: [prs_india] fetching https://news.google.com/rss/search?q=site%3Aprsindia.org+when%3A7d&hl=en-IN&gl=IN&ceid=IN%3Aen
09:07:19 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=site%3Aprsindia.org+when%3A7d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
09:07:19 INFO    grounded.ingest.google_news: [reuters_india] fetching https://news.google.com/rss/search?q=site%3Areuters.com+India+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen
09:07:20 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=site%3Areuters.com+India+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
09:07:20 INFO    grounded.ingest.google_news: [ap_india] fetching https://news.google.com/rss/search?q=site%3Aapnews.com+India+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen
09:07:20 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=site%3Aapnews.com+India+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
09:07:20 INFO    grounded.ingest.google_news: [the_hindu] fetching https://news.google.com/rss/search?q=site%3Athehindu.com+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen
09:07:21 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=site%3Athehindu.com+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
09:07:21 INFO    grounded.ingest.google_news: [indian_express] fetching https://news.google.com/rss/search?q=site%3Aindianexpress.com+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen
09:07:21 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=site%3Aindianexpress.com+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
09:07:21 INFO    grounded.ingest.rss: [reddit_news] fetching https://old.reddit.com/r/india+indianews+IndiaSpeaks/.rss
09:07:21 INFO    httpx: HTTP Request: GET https://old.reddit.com/r/india+indianews+IndiaSpeaks/.rss "HTTP/1.1 302 Temporary Redirect"
09:07:22 INFO    httpx: HTTP Request: GET https://old.reddit.com/login/?reason=lor2&dest=https%3A%2F%2Fold.reddit.com%2Fr%2Findia%2Bindianews%2BIndiaSpeaks%2F.rss "HTTP/1.1 200 OK"
09:07:22 INFO    grounded.ingest.rss: [reddit_cities] fetching https://old.reddit.com/r/mumbai+delhi+bangalore+chennai+kolkata+kerala+hyderabad/.rss
09:07:22 INFO    httpx: HTTP Request: GET https://old.reddit.com/r/mumbai+delhi+bangalore+chennai+kolkata+kerala+hyderabad/.rss "HTTP/1.1 302 Temporary Redirect"
09:07:22 INFO    httpx: HTTP Request: GET https://old.reddit.com/login/?reason=lor2&dest=https%3A%2F%2Fold.reddit.com%2Fr%2Fmumbai%2Bdelhi%2Bbangalore%2Bchennai%2Bkolkata%2Bkerala%2Bhyderabad%2F.rss "HTTP/1.1 200 OK"
09:07:22 INFO    grounded.ingest.rss: [reddit_topical] fetching https://old.reddit.com/r/IndianEconomy+IndianAcademia+IndianDefence+geopolitics/.rss
09:07:22 INFO    httpx: HTTP Request: GET https://old.reddit.com/r/IndianEconomy+IndianAcademia+IndianDefence+geopolitics/.rss "HTTP/1.1 302 Temporary Redirect"
09:07:22 INFO    httpx: HTTP Request: GET https://old.reddit.com/login/?reason=lor2&dest=https%3A%2F%2Fold.reddit.com%2Fr%2FIndianEconomy%2BIndianAcademia%2BIndianDefence%2Bgeopolitics%2F.rss "HTTP/1.1 200 OK"
09:07:22 INFO    grounded.ingest.google_news: [google_news_india] fetching https://news.google.com/rss/search?q=India+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen
09:07:22 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=India+when%3A1d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
  389 inserted, 0 skipped
[publish] embed...
09:07:22 INFO    grounded.pipeline.embed: embedding backend: voyage (voyage-3)
09:07:24 INFO    grounded.pipeline.embed: embedded 128/389
09:07:25 INFO    grounded.pipeline.embed: embedded 256/389
09:07:26 INFO    grounded.pipeline.embed: embedded 384/389
09:07:26 INFO    grounded.pipeline.embed: embedded 389/389
  embedded 389 item(s)
[publish] cluster...
09:07:26 INFO    grounded.pipeline.clustering: formed 291 clusters from 389 items
09:07:26 INFO    grounded.pipeline.clustering: created 291 events
  created 291 event(s)
[publish] rank...
09:07:26 INFO    grounded.pipeline.importance: scored 291 events, selected 25, demoted 0
  scored 291, selected 25, demoted 0
[publish] scrape...
09:07:26 INFO    grounded.pipeline.scrape: scraping 81 item(s) for selected events
09:07:26 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMirAFBVV95cUxPa2FTdGRsWC1rQWRzSzdqLW1FcFlGR1k0Y2MyTGwtMGJuN01NeFp4Q3FVOWVjeHBueHNwYnlpd0FSM0ZWTkgtVEJUTGZaNmlwbTJxemVnUmg4XzVJOEoxTkxKN2xIWnU3MnYtR3BsekttSDB6SkNYUzB2ZS1YQ0RGblFNY2tlTlBDR0g2UlVzaGRMT2pwZ2Q0RVE3dEMwcHNaRkhEQnBpeW5CQlRr0gGzAUFVX3lxTE1UbmJ3b2xDVWgwdHBuTm5ENUJ5YjB2dG9jR0k2OEZEX3czZHBsSDR6YU9RMnk5MGJrUFpNN0hMNmc1U0h6MTNkY0xRZTJLVGNGeUJiZVFKVl9teW93cWxPTHVVRWNIcVRmSlZlOHp6QmJkMzJZUVd4TFliQ0V4MzMxUjB2OXdMZ0d5clVqVi1YRzB5cGNNZC1NeUlnYlZienIzZ0lkSGYzbmhZWV9PeDhNMzVZ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:28 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:28 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:07:28 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/legal-news/brij-bhushan-acquital-sexual-harassment-wrestlers-wfi-10893647/ "HTTP/1.1 403 Forbidden"
09:07:28 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/legal-news/brij-bhushan-acquital-sexual-harassment-wrestlers-wfi-10893647/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/legal-news/brij-bhushan-acquital-sexual-harassment-wrestlers-wfi-10893647/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:07:28 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiiAJBVV95cUxPQnI5TDlOOElqekU5aWl5RUU3Qkx2Z1lkaEk5TEVQOEh4MWNWNHVjN3RfZWwzSk1nWDRJZDM4aHAxdFZsWlhUNDVCcTZOR2NXbnlOSXFwcGlzbnVzdlBWc0pCTUgtd19yZUNiQXhvb3prcC1aTkhkZXplSlc1a3ZLdmo4MjR4dWFNSV9mSTd0d2wyR3U1X0xjNEZEY19BdWJNdkVkWFN2QmRXYTAtc1lKa3lhR3JRTDFGcmxmc0NNcERBRVQ2SUVMaWowM1lpcDFVdFFFZFduTU82blNWN2RQaVdiS3FLa1ZXaWpSQk41dk44R251cTFOR2VQeEgwMjNSM0dqaHVDTTHSAY8CQVVfeXFMTWVWZWkyVjZDQXhMNlI5dG1PX3dYMGFVRUk5VzR5cVRmU3RWQXFrYUxoWTNSa3IxUkpRLVR4WlIxb3o2cHZfUW0zamZ5LTZHYjd0WFEtNU9IdVlOWDdtMkhkd21nRmpVb2lLeXRGRTBmMnA5VHZzaEotTjVhZmNaU3VxSkhrcW1RUFVGemdzTXRKckloZXJmWW5xWGNPVGVnalFCaV8yS1RrR1JHVG5uYnJUZGpFN3cwckhsMVJvNUpVN3dmNVhkaDVpU0tjazN5dU0zNU9HR0JOdzFmVGtnZWZ0dHN5R2Fra2lqRXdVZUc2ZGFiSEY1eEpRVUhGLUVfeHlTdDFmdlVGTk5zV2pxRQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:29 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:29 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:07:29 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/international/shehbaz-sharif-raises-kashmir-issue-at-unga-credits-trump-for-timely-intervention-in-2025-india-pakistan-conflict/article71511517.ece "HTTP/1.1 200 OK"
09:07:29 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMisgFBVV95cUxNMVl5UWZyaGVDLUl1bjRtSGF1ZkktWG84Nld4ZzVVb2NlOHhVZUgtRzY3NF9PdDFqZlRYbDlhaGtMNm9wdHBuRm4zR0NUazY5cmhQZGtuOVBwbW44Ry1CQ0pKRVFvVnlsbkd3ZElYQ1pYU1pOMjZJQXJXMlZWUkRaUmtZaDZRUjRfblpLWnhGSDQ1QnozSEMyeFN1QmtuNzRsZFBFSVR5aVdUMVA1WTM0M1dR0gG4AUFVX3lxTE15dG41TjBLTnR3b0NhM1F0ckNZNkhORXdacmFSZEowT2FReFVQWmh4MjdsUXJNMDkwcjVLanE4T2FIYUpHOWZLRXdlbGhZRXRna2RUdWt0OU1vcUI4djlZOEpOdzFuYU1BUmR6ekhsT2R3T1l0eWN2SVFYRjFOYnVCdVVKQjJSRVFNdXhxZjBFakFfTS1tZmltcDJPVUJhZnhsTTkwSDJkQmpIRGFXRDZyU3ZsYnEyWjk?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:30 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:30 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:07:30 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/cities/delhi/rajiv-rangila-rs-700-crore-delhi-medical-supplies-fraud-10894234/ "HTTP/1.1 403 Forbidden"
09:07:30 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/cities/delhi/rajiv-rangila-rs-700-crore-delhi-medical-supplies-fraud-10894234/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/cities/delhi/rajiv-rangila-rs-700-crore-delhi-medical-supplies-fraud-10894234/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:07:30 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi2gFBVV95cUxNdnNYZl9SWHZrbUYzQTEzU2FxR09PcDdCdVVicURHUmNkdnFURmdrNXJBTGgyMG9JRVVPQ29lbDlKU0JCOUdEMDJiQ2UzMFh4VXAwcjVCYVBlYVFxRVN6dHR5Rm5IaGFfaEJiOFNkaFpyZE9Ddy1rZGRVak1YMl9Cc2R1bEwyMWRrMk9OMHRUcGVVbmtJQ1pJR3Q3RWZ0dmpvaXJpdXB5WjZxcVctdHFVWXl2cmRpd2J5NGJSVHM3RmF1UmVYUTl6OUhYeE9wQ3JnbkpSUlNFVm83QdIB4AFBVV95cUxQUUo0cDZxbDR0Vjl2QnBMQ3E1elVMS1RUMTdMMFpOa2hwX1hBWHg2M0ZEcHd1LWU1eHNIZWZ2ZHdXTDByTk1xczhnbTNicGpNem5MMWtMU1RiUTNTdGFKeU45SzZRWGhQQjNGblBnVXFfUnRhT2FnWGlPbm16RzY0VFIxSUQtMUk4eGVLQnhwUVQxbEJEZzB1TkhUMDZFN09YNzV1TG16aE4yY1hzUV9weEk4bDlrTU94dHhOeDBTVXJnOW9lcDl5d1lOQzUxNVlWeWpiM1plNzlEYWM0TnRsbw?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:31 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:31 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:07:32 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/education/iit-delhi-innovation-researchers-build-homegrown-gpu-graphics-chip-ai-computing-jee-main-10893538/ "HTTP/1.1 403 Forbidden"
09:07:32 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/education/iit-delhi-innovation-researchers-build-homegrown-gpu-graphics-chip-ai-computing-jee-main-10893538/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/education/iit-delhi-innovation-researchers-build-homegrown-gpu-graphics-chip-ai-computing-jee-main-10893538/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:07:32 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi0gFBVV95cUxOR3hkT0ZFSE84aWVpYld6OXZyZG9jajJKUWxDM3lkdjdHNXN0Tm9vU244MkVOWW9OTkwtZXRPQXdBa05sc2VDSnZaZlJJRWJRVHc5MnVHeHJmQUNXU1M2djRPcUV3Z1dfaW94WmhxVHJROGk1TTZvemUzNHhrcGhja0pmQ041V0ZSQk11MW9qUjlORGtFTjF1c1lyRkxKNW8yTE1IT3NpQUZVRkZKeG4wdF9aQmotdFRjRlNGaFdUMFFsU3hob1c1VkZKNnU3cXkwRmfSAdgBQVVfeXFMTzlBRi1CUi1BMndqUVFhalRNdkdLTVNpRU85Z2VMWnBJR0swNnp0RThHWVp4eTFqbE5lZC1wZXJ1RHpGMEFIbncwakotek9RV0tFdXZVYUVHTVVqRGpOVGttY3dWa3VSU3dRRVF1X3c2RmZ3X21FdThzMzZiOTlkQTRRckpLZ3djZmtYbm9HajdMbFdqd1FQNEJDUF9Cd2FrM0sxbUZiNGJOY3ZPaXJSOXZiQTZfVXRvYkdaeDl6cF92SVpxd2VDQ2NZSHBWMG11OEg4em1ndUt6?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:33 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:33 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:07:34 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/legal-news/delhi-high-court-cjp-police-protection-woman-pm-modi-deepfake-meta-takedown-order-10893935/ "HTTP/1.1 403 Forbidden"
09:07:34 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/legal-news/delhi-high-court-cjp-police-protection-woman-pm-modi-deepfake-meta-takedown-order-10893935/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/legal-news/delhi-high-court-cjp-police-protection-woman-pm-modi-deepfake-meta-takedown-order-10893935/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:07:34 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMixAFBVV95cUxPSFBIQkpuSEllQm1DNjJjOWlUV0FGX2pvc1NCZmotenJvQnYxWjlkSUtURDNMUXZta3NUY2N2amI2bW1DZUFWaFF5VGlSSDZLU29sMWdWaWxqWEU2cUNFTGdyVkpDRzRncXZEb1dkNy11b1VBNHZQRERjQUNQTU1PWms4Q0I3Tno5Y002MkRoejZQajUtMmlNR0JZV3BwcEJONHBMcjVQV2ZzRjhmRFF2T1U0bzlUVkdpREswYWpmempNSWst0gHLAUFVX3lxTE56dGxfNHEwVWJGZmRtVXg0MEVhTWd0Zlgwa3k4NjJ0TGpKWkZTRXg1dUVLNmpYcE9Jd1l2WC1hSkZjR04yTjRYYkVvd0pzSWZRSHg1UUpTR2twMlY4NXdtUFJqdmxSOW5VUUduR05sOVg3OTRFTnVHeWctVVM5NjI2N1JqVXhzMUNMV2dRbFVENUNGcDZVMkRsREtfb3lXejhvU2pvTG56RGQ5QjlNclkwcnp5RmpTUTRSZW9aYVhSclk3UXVLV1NXZG1r?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:35 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:35 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:07:36 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/world/pakistan-pm-sharif-warns-india-conflict-un-indus-waters-act-of-war-unga-2026-10894412/ "HTTP/1.1 403 Forbidden"
09:07:36 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/world/pakistan-pm-sharif-warns-india-conflict-un-indus-waters-act-of-war-unga-2026-10894412/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/world/pakistan-pm-sharif-warns-india-conflict-un-indus-waters-act-of-war-unga-2026-10894412/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:07:36 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiaEFVX3lxTE5wQVB0WVpxU2JkZDg0T1RfMzgwbVF0MlBCeEVUMl9ZaXZab3FseFY0X2t2QVJyNGpjbWloTGVzMS1xUWpQTjgteVQ5OVBJNmJiWHFRUk4yMlhiUkdkODA2bDNJM3g0VTlT?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:37 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:37 INFO    grounded.pipeline.scrape: decoded Google News URL -> m.rbi.org.in
09:07:38 INFO    httpx: HTTP Request: GET https://m.rbi.org.in/scripts/FS_PressRelease.aspx?fn=2757 "HTTP/1.1 302 Found"
09:07:39 INFO    httpx: HTTP Request: GET https://rbi.org.in/ "HTTP/1.1 200 OK"
09:07:40 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMieEFVX3lxTFB5bWpqNGhtRTVPNGRab0lGX0hJZDdVVEgxeFRuSEVJWEJYZkJyci1UUmJKYjFfNUl3UmJMZjY4RF9HeV9obkJoUURwUnkwckkwek1QSGFJNVZJZXJTSDFuNzNvTHhmdmZiODlCWTh6V05zRDdMa0lmWA?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:41 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:41 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.rbi.org.in
09:07:42 INFO    httpx: HTTP Request: GET https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63669 "HTTP/1.1 200 OK"
09:07:42 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMixAFBVV95cUxOMXlBbVJkdmVUVmtEbHAtNkY0TmRzc0xJVG9xN0tNdWMwRnhlWWhtM0RnQWdERGdrdlc0WkZseHQ0Sk00RldlV2c3TjhEWW5MQ3BOVFhGb1h0SGZfMDVNc1pIeEUxV292WWdOYlB4b1JTc19raGx5T1NQQnBaYnRCNExCeHlTQ2M5aXhVQU5VdVZjVXZrX3daRWR1Y3YzVk5EbVdla281cFl5MTBYV2hKa3pDVnhBN3EwT0VwZ2lZcVpCVHM30gHLAUFVX3lxTE5lYmZvR18zSVlpUWVFREhjNjhYOHN5Ui1vb18wdTlNWDdjZUtKXzFsaG15ZXIyM3BRczVKSjRfcG5scUpweTNMVmVtZ2p2UkZyRjkwZXpqZGhfRWpUMGxZTndWV0YwLWl2aldPZnlNaFRHbVpwVUVWR0N5VHROczNGUHk5N21PYmFTQU1TZmNNWUxsZFZSTk5fNUVMRWdWN2prWjBsMXBFRmhVYnd5RkRSb3NQRmd0S28ybXVtT2xsZXNNZFpBdVR4dktz?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:43 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:43 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:07:43 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/india/chirag-paswan-cec-gyanesh-kumar-clarification-eci-internal-rift-rahul-gandhi-10893444/ "HTTP/1.1 403 Forbidden"
09:07:43 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/india/chirag-paswan-cec-gyanesh-kumar-clarification-eci-internal-rift-rahul-gandhi-10893444/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/india/chirag-paswan-cec-gyanesh-kumar-clarification-eci-internal-rift-rahul-gandhi-10893444/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:07:43 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiowFBVV95cUxNYUVaTThEUVQwNGNnNWc3SkloR0dEeThINkJqOGN0WW5QQWlsamxIeU9LajVIb2J5YXVpLW1sNDJsY3NTVE8zbm15T0Joa2g2RkxUVGFNSGFIQmhoUldLX2IyQzVZbEVNUzJVME5XSDhmRmVMcWtJbmxNaWpGbU9GeS1haTg1OUJoQ1VEYWZXNjdZaW9jblB5S0dZZllET1NFZ3RR?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:44 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:44 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.prokabaddi.com
09:07:45 INFO    httpx: HTTP Request: GET https://www.prokabaddi.com/features/asian-games-2026-kabaddi-day-6-live-updates-scores-results-finals "HTTP/1.1 200 OK"
09:07:46 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMieEFVX3lxTE9naDhZRXYzUkk1SDVxT1p0RHIyNDN2OC15d3NSU0RiVzBtVDNRTlhDcndHRnhxTHBIZXVZeEpYVFhXUFd0YnQxejllZzBJWUg1YllteDU1RlpuR3MwRnBKcGFrUC1FQTk4NlZGZUZlSVNEaUxFczdIdg?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:47 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:47 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.rbi.org.in
09:07:48 INFO    httpx: HTTP Request: GET https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63665 "HTTP/1.1 200 OK"
09:07:48 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMipwFBVV95cUxNZi1pRXBVWjNyZTRTa2RkTG5XRlM3VnR2eEZuODFyRFZaTW9MdjdCUVRoZ2dtSzhORG56V2o1a2I0blFLTWl2WFlfdDFZbVBXUEEta2QxNGN4dU9wamdCSFFEVktMT0pWTTBqajJMa3hhNWtSMkZyYzdjdmxjUFpfMjRqYk9DRC0xaTA1bzIyZHdQUm10eXRPdVJyZmFYV3FnLWRBUkZlMNIBrgFBVV95cUxNQ1I1OXluRUxxUnBpeElkdE45U0I4OTAyOWtBajVnSFVIZS1TdXJ2ZmUyUUJPZnJwWjBxalhNSVZJeDRhcHdPMGtzSEVraGltdjdhSGYxV0dZU0s5eDhuanpsbGhnU19iNFRoLU9IYmJZVlM0b2FoNTZ0WDRMVGJOQVV3Y2JKb0tkazVRdnZIVWJPcGRBcDE3TUlWRGpHSk9XblZQc25lNlRITWZnSlE?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:49 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:49 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:07:49 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/sports/asian-games-2026-medal-tally-india-gold-silver-bronze-10893706/ "HTTP/1.1 403 Forbidden"
09:07:49 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/sports/asian-games-2026-medal-tally-india-gold-silver-bronze-10893706/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/sports/asian-games-2026-medal-tally-india-gold-silver-bronze-10893706/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:07:49 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMijAJBVV95cUxNcmFLUldQTTRLT2V2bFdTS1hGR0czb1MtRy1SXzAweXJQRVQ3Vi1FcmlDclNWQ0RQLWdTNXlNU3ZWTWtBMDZyTFc4U2ZMVjl6WmFXLS1UUG02dV8xNDFIN0tyaHprcU5jTUJMNDlTYWVDLVhaeDdtb285VERWenB4bDVjenQtTVI2MEREN3hEcmlJQ0pwUklTTkIxZmNWam94YTAzZ3I2X3BNSURDVnZrbDhmeHJFWExXOW1tLUdtRkNiaVBNUmszWkpCVUFVTkY5SnU3ZndpUG5ZcXFsY0pVS1ZvSDRpR0dOeXVfN2Nha0dtUmg3OHlYaXZWaVJwWGUyYXdBNE9YMEUzUG5R0gGTAkFVX3lxTE42UEtmXzhZcVJSX0J3bUpmVHBMSmd5NGxqZ0puZ3gzUEpCbE1DdW5GM1NaUFVPUWpsSG1KTGZ4YVI3bUJJdTJhd2dQWG5sZzlfZ21VX2p4eDczdkNsOG9hVnVTckxZcUhwbk5RcjN2TG9FS0sxOXY3M1BLM294dUlneVRsTW1OdWhfelhyR191b3B1cDAwajFqeTloZHZIUXIxcV9TTWpSSDRCaUtKaTJyR2xhZ2Z2b1hzSmV0R3ZwSGphUXpCcXhpbTVzWkJwMGVUNTlIMW1uLWZZT1JlSm9TeU1OeDA2NE1xZWVXSUFFYm1Ud0ROeUtHZjYxVE90R0Eyd0UxWTlfUFR2aUp0QUFWU0hj?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:50 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:50 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:07:51 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/education/tamil-nadu-skill-development-vettri-thiran-payirchi-thittam-ug-degree-additional-skill-course-naan-mudhalvan-tnskill-tn-gov-in-10893631/ "HTTP/1.1 403 Forbidden"
09:07:51 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/education/tamil-nadu-skill-development-vettri-thiran-payirchi-thittam-ug-degree-additional-skill-course-naan-mudhalvan-tnskill-tn-gov-in-10893631/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/education/tamil-nadu-skill-development-vettri-thiran-payirchi-thittam-ug-degree-additional-skill-course-naan-mudhalvan-tnskill-tn-gov-in-10893631/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:07:51 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMingFBVV95cUxNOUtTUUlwOWY4T1c4OEdaQUk2bEx1Zk12Q1BSeWpySzBGMU9EU3ZGakRwU0hlUDlLUWM3RllOYUZCbHh5X1lEV2xQMHd6WlZYYWxxYzlSOWdBTG5UQXN3NGl3NmxwZDZ4WkhwdzFucnFRYTVSUUJIWWVzWVVzWS05UDZ0Y3BPbEtMc2lTQmNtbU93elpVaXU3alN6VUVSQdIBpAFBVV95cUxQVHZZZEZ0MGpJVWUyVFI0YTF4Uk1mSlZ1OW9IRkdEOW1qNTRIQThPSktWWDRFMDVZNUM2X1ZsSlN6MXc3b1B2dEFCZ0NTWDZOdThrenVod2RjTzl2MW9VTE9GN1lkeTlWc2o0cmNZU3RJUDcwWHA5MllQaGt1Z3RQMERrNzBKb1dxcThQNG9JcEZGQzkxUHo2QTQ5Si1YQVlkSjg4bw?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:52 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:52 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:07:53 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/cities/delhi/gangster-dhila-wedding-custody-parole-hc-10894070/ "HTTP/1.1 403 Forbidden"
09:07:53 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/cities/delhi/gangster-dhila-wedding-custody-parole-hc-10894070/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/cities/delhi/gangster-dhila-wedding-custody-parole-hc-10894070/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:07:53 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi2wFBVV95cUxQeUVOUXIzZ1F4SEg0a1p5T3F0Ny1BY204TE90ektERkRUekJ4b1p6WmlqUE5YV3hrMHBBNTY4aVVQVFJGeER2Mlo4d0hIalZmaE9nQnA2aEt2UkQ4YzBzV2RXLXhCMjR4dnlOU0hxUnFZWmdaUjVrSWs1QzZxbnBwUnNwdGpfalVnUzVuaF9qQllqME1GU1JHZlBKbmJOclVKZG9fWGRYQTBUUGF3UkFWOFJCM3VjdHU3dmllejdwbExsS256X1JzZHRVako0X2ZqWkItWTA3aWoycEHSAeABQVVfeXFMTng3ZFMyRTFweE9ZWnlmUlpiMFVPdmVBLTI1SVg3cmhFam5JWUQyZDRJei1xbUFuV2tSZE43aTE0Y1dnSDRjZ2JtQ21hb3VDbXFIZXlsV0lmVWNUVW5JTDFMRGJXRkoxNkJYSHZrTUFCUUtWZmJDa1VRRVV0RXNkU2xkN0hlay1RRENyRkRaYndNNE5PSTVseDRoc3VpZl9BWkFpUWd1c25vanJmQmkxRjdUelBKYUpjRWRVWjhoMXU5UnNsYnI3TGNxZGhKR213dXpJYXlwLU82endQOEZ1LUY?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:54 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:54 INFO    grounded.pipeline.scrape: decoded Google News URL -> timesofindia.indiatimes.com
09:07:54 INFO    httpx: HTTP Request: GET https://timesofindia.indiatimes.com/world/us/hypocritical-homilies-about-democratic-rights-india-flays-pakistan-at-un/articleshow/134495894.cms "HTTP/1.1 200 OK"
09:07:54 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMieEFVX3lxTE1zYTM4MHVnb1BRb2kxeHlHakJMdDFTMTVDYUlzZzZHbW5ZV2ZhUEJJR2V3aW11Ynd0WXhCN1JOR1poZzFmbm9mYVNOWGJ0dEU4dEZ4QnptdUN1czhGM1d1X0F1d3hhbHV5eVRNMmtTYUNYVFgwanB5TA?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:56 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:56 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.rbi.org.in
09:07:57 INFO    httpx: HTTP Request: GET https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63674 "HTTP/1.1 200 OK"
09:07:57 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiqwFBVV95cUxPaFVoSzM4WHkxOFMwVmlDZWc0a3U5blNsNXdlamF4VG5QNHNjTGF5YXdfNjlIeThUWm1ONTQwZ2RDZ2Rvc1JVbTg3c3ZSTG1ROVZWM0ZDam5NU1pqTDdvUi1CQXhEVGJlczBhMzZlelJRaUc0Z0lHVEt6bmRuMGVNV1BObUQwY2c1Y3dhdmlScnZYdFNpMjduZ1ljRHo1M3d0OEpuN0pTTGF2MlXSAbIBQVVfeXFMTlVrTXlyclZXcVFMUk4zZTJKRW5Kb20yUlZLYjFfcWp0aThyY0ZwQ3p5RWVkNWl3Um1pVTBLdHdzdDZ1eXV0QnVfbl9XX0ZmbGtqV0ZUWHY1ZlpqdXhURkd5NGJMSGdqRzJtdGZQRFVDSmJCcXRHTFBFTDZLTDZtZjZWZG1JMTVvaHlBOWFxRm1kc0VIUThLYWg1U0RnWEdldGpwZDBsNnpzdFhwenc1SDJuQQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:58 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:58 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:07:58 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/sports/india-asian-games-day-8-full-schedule-fixtures-time-list-10894281/ "HTTP/1.1 403 Forbidden"
09:07:58 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/sports/india-asian-games-day-8-full-schedule-fixtures-time-list-10894281/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/sports/india-asian-games-day-8-full-schedule-fixtures-time-list-10894281/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:07:58 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiakFVX3lxTE1xSUhUWHZpcFg5RzVJVHNtZnFaekRwXzE1OTNEWnJwYlNIc1cyM2JQem9xbmhmMlF5V05GWHN2ZkxaV2hDa2Q2N01ZZnRCemp3OEt6MXNNaUd6V0hEMThJVEJPczI4ZjBSVFE?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:07:59 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:07:59 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.rbi.org.in
09:08:00 INFO    httpx: HTTP Request: GET https://www.rbi.org.in/scripts/bs_viewcontent.aspx?Id=3990 "HTTP/1.1 200 OK"
09:08:00 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMitgFBVV95cUxOc25id2RKd1BoanI1UEw4V3lwaHU2TFBzV0V0WTBGZkducWY2VTVwTWhmckxJb21rSWtwdDR2MWtZMFY1OFJuRGtVOGQ3cElMRDc0bld4RmgtZ0hjUFU4bEJiOTBmMnUwRkhZZlBzY25wczMzMFBoTEdiR0ljdS1OZjMtM0xaZzBvcmloRzVHOUVkV2c2QUlhY2phUWFvVUYzUUFteGNsdjBsbHZQMUh1cUJlY21NZ9IBuwFBVV95cUxPUzVFLWlqMHVKd2xxbG5qMlpHY1NUbXV0WkNKaUM1V2NBcHBOa295eWxRUkdlS3FOdFl2WTVmR1IzczFUWXRDcmZOUE5zMlhsbVN1cUFoVHdKMzVhdDItbDk5blhwSzVoVDRCYjNtVXlSYUhXRlhLTnpCQ3NJSjdOQUJrNUVjWDFuekd3X19BVnN4b0puWXExWVFydWM1SmlpNkJFN21QbmhRUFpXYUpTZXk5b3BldTRqc1Vz?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:01 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:01 INFO    grounded.pipeline.scrape: decoded Google News URL -> theprint.in
09:08:01 INFO    httpx: HTTP Request: GET https://theprint.in/world/after-shehbazs-speech-india-warns-pakistan-at-unga-of-consequences-for-terrorism/3054100/ "HTTP/1.1 200 OK"
09:08:01 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMixwFBVV95cUxOUXBtWi1sV1o1R29SRUdlTlVwZjZ1OEZMa2FPV2EtOHloX3ZGZkVHa0JHcUwzaE01Unh4TDRTVFZwTmJiS3FYZXR0U1N0RUQ1aGdiUlNnazNEbmR3ei0takplNWROZVVFZC0yaEJ2RjgtTHg0QS1oX0JMZkFvZ3dYQlV6Z1docnY2WVh2QW5LbVpZN19Ec0swdTM0bEM5YW5UT3ViZHpDdTczZnRlU2lNNzdQaWtwTXFpWHpOdHNiVTU1ZG95b0pN0gHMAUFVX3lxTE1LS0pRYlJlVERQVkMzOWRtQXFZaDl1QjFvTXJKc3hOZG9KMW82MWpWTERlYmliWF9Zbk1nZHN2M1pnWkhKTHNpaHFtNEpDaHA4SmoxMEk4LXVVZldYZEdOTUpacDdHdWUwdnJhS1czSmc5QVh3TWhXVWZWZVdWSVlWaGFuLW9mX2tMdFJzZlNod0VaTU5ycGNYcjA4dWdXcjg5c3JLVGYwQlVCeTdvamVNZ3pNTXVsRWJvOWNnRGQxd3h5N1hNVko4bGhOaQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:02 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:02 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.etvbharat.com
09:08:02 INFO    httpx: HTTP Request: GET https://www.etvbharat.com/en/photos/in-photos-india-women-clinch-4th-asian-games-kabaddi-title-with-win-over-iran-enn26092602890 "HTTP/1.1 200 OK"
09:08:02 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMingJBVV95cUxQenZUYjlEUWRZOFowY1VLeElwcFVtZk1NcDdZVlp3TkxMR1FvYmplcGh0WnR5eXJxVG55Y1I5MVlaVFhMRFItU0pXUC1fVWlwS0xGOVl5blBjS3UyVE5TcEtHMF9yTXRkM0d0VExYem9OcjhzRi04aVVSdElVLUNYdU5GYko0NUFKdjhic1ZkNHpMcGV2RWNTejZOMHFFMzBFTEhPWkZ4Z3Y0c3NaSjFZTUp4YmEyUjFac0lZdE95bklQdmdPT2FvdWpmMFN1WWF4WkltUWllMkp0X0ZsQU9PekpneUgxZkdCS3B5eTl5NmktTS1DVm5Td3lsRzlVRk1QSXluLUpCUi0tdWU0Tjlaak82ZTQwZ2xCaTFGNEN30gGkAkFVX3lxTE9GbTRNTTM1OHdPNWM1VUVJOFNNOFRaVFU2Q2M0bmRqVVNaamc0OVFCRXY0NnV5azhneEx3aFUwakx2VXY5U25xaFgzeFcyT2pLRXdiU1VYSWo2NDc0Z3pBZlBiZ3BBTXc4T2d3cDlJQ3FHNW96VjB1U1V3WlpsMVR6QVRoTHNuZTdJcTFGdzNqZGJHQ2dVUndqWXNHd0FTN1E2WVZpR2V1YzBTYW9YTXFiWjNqbXdDVWRRbDVObWZRLTNEMlRWX3RxZjZBMVJSOGFXMHZLWUtoMWEzUGRIVkRiVE5vc09OOVdLZGQxNW1KVy1kVzh4UmZjTlJ3MktqbVpMZzhnRk9jTllaaVk0QkFuNXBlLUdCVFRKYWw4ZkxHOWxzSU4?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:04 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:04 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:08:04 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/national/west-bengal/bjp-manufactured-narrative-and-created-religious-divide-ahead-of-west-bengal-polls-through-youtubers-says-tmc-spokesperson/article71509269.ece "HTTP/1.1 200 OK"
09:08:04 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiZ0FVX3lxTFBfRWFvVXFoUDd1VE9QaWk3RVdoLVdpUVR4QV9UckJjOFhyVjhwd2hqMmlsdWVoMGpocjE1R0hIaXdyY2Z6cFpod1djY1U0a3ByMDNsT05EdlhJOHZVT25BbU5xcEJpU0k?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:05 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:05 INFO    grounded.pipeline.scrape: decoded Google News URL -> m.rbi.org.in
09:08:06 INFO    httpx: HTTP Request: GET https://m.rbi.org.in/Scripts/BS_PressreleaseDisplay.aspx "HTTP/1.1 302 Found"
09:08:07 INFO    httpx: HTTP Request: GET https://rbi.org.in/ "HTTP/1.1 200 OK"
09:08:08 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMikgFBVV95cUxQLU9QaE8wZU95MXdGa3IwRkVFXzJHS3lPR1RMR25lUmFJRGFreXlKSTBoUXI5R2c2a0I0dHFDMDhTemY0bVlwWTd0SFRmeWc0dFdFRWFGd1cwdUhLOFpSSnRNbGc4UzJCV1c3OHJqeHdPTUdjUU81eURKMmFNNnNUZGVFUWhHX1Q4Z25qU2xYUkw2UQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:09 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:09 INFO    grounded.pipeline.scrape: decoded Google News URL -> prsindia.org
09:08:10 INFO    httpx: HTTP Request: GET https://prsindia.org/files/parliamentry-announcement/2026-09-25/FCRA_press%20release.pdf "HTTP/1.1 200 OK"
09:08:10 ERROR   trafilatura.utils: parsed tree length: 1, wrong data type or not valid HTML
09:08:10 ERROR   trafilatura.core: empty HTML tree: None
09:08:10 WARNING trafilatura.core: discarding data: https://prsindia.org/files/parliamentry-announcement/2026-09-25/FCRA_press%20release.pdf
09:08:10 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMimwFBVV95cUxOSUQ1RTQtVVN2cG9paVVyUmpadF84bUE5c2x2bS05VkRaOGU2aVVTNy1CUmJqTG1uQVlGWGZiZkJteHFncUtOX19iU3FzZW12OE1xdmZKQWE0RFVubU4ydEJYdnF6NDh6QnYyUU1WTmd5emNOS2VXaHhMeDZmY2Z0cENfdmJ1ckhfYVFVdG92YUF0b1dmcVpDRFY4NA?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:11 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:11 INFO    grounded.pipeline.scrape: decoded Google News URL -> newsonair.gov.in
09:08:12 INFO    httpx: HTTP Request: GET https://newsonair.gov.in/india-women-clinch-kabaddi-gold-indias-third-gold-at-asian-games-2026/ "HTTP/1.1 200 OK"
09:08:13 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi1gFBVV95cUxOekVET3VqRVdwR1NVandCTHpvUjNxNlBvSl9PaUJXRmhaaEtRZ2hmbTNRSHkzSFplTWJfMUdVRmZ0UE9TclM0bGFZWVdlcDJWSmxxNUh1V3pkZUx3RkI4M3E2dVlqNDJMSkF6OE5JMmY0bVVza19NeGVmQktsU01ibG1aUExqMEc0b09pVjJxNEVwMThqeXpNRzhhUldETW50LU9PR0xLOFVaTzJwQmx3T1hTclJ4TzE1dzBKWlRiWXBvWDZWTjRZY0thcGJ5a19sbnF1Q3pB0gHcAUFVX3lxTFBqWFJmbFZLUUY5alRaQldaYXBHTVlpWXBWOENJT1ktam9nZm1ENjlfRm5HY1lNOUQzcUQweWVOeUZUYWYzZUJTd0gweUIzMmlmMy1INnMtbVFRSHNpNTRKdkFtdzlxU2lvaEkyWG9rUGJyYmljZHRDR1oxNjBDZGhLRjRoY2R4UlNnSEdqcFdycDhZbVMxZkQxWW5MaDNrR2dId1BZVXNOaC1walYtaHgweU5TbHhZVktFcUtsZllQbWNURFdudlpiUXVvendLdWRBSXcwUmI4eUw5NjI?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:14 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:14 INFO    grounded.pipeline.scrape: decoded Google News URL -> sportstar.thehindu.com
09:08:14 INFO    httpx: HTTP Request: GET https://sportstar.thehindu.com/asian-games/asian-games-2026-india-wins-gold-medal-womens-kabaddi-final-beats-iran-score/article71511675.ece "HTTP/1.1 200 OK"
09:08:14 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiZkFVX3lxTFAwTUdtVGVOSUY2ZzZDdUphRENUWE9DZTcyYUJuZmN2VmFDM21lakN4THVhS1NWOXpNOXYyVlo4NXNBRXl2U1B3NDA2eEs4dmVqenI4M2FNUTl2U0ctVVZIVmNHQ0EzUQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:15 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:15 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.bbc.co.uk
09:08:15 INFO    httpx: HTTP Request: GET https://www.bbc.co.uk/sport/football/live/cmn8ep4e525wt "HTTP/1.1 200 OK"
09:08:15 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMinAFBVV95cUxOMzY2LTVDNGxZMGJqVERhNnpYMDk3UDM2VmVmNE5CWDdSVS1Nb0VDWVF4cFBlZ1lzR0RoUzB6Rm5nMHU5RkgxT0ZCNWx2Z1FBNnB3UmZuZ0pZd25pU0xYZDZscjRtLWtzeW04V0tjYU83VWtKVkF1cTdfRE5QcllBd2ZvWFBEdnM3SjljdGwxc2RRUWFqZXhiRlZlNXA?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:17 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:17 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.olympics.com
09:08:42 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://www.olympics.com/en/news/asian-games-2026-kabaddi-women-india-vs-iran-final-match-report: The read operation timed out
09:08:42 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMisgFBVV95cUxOX0JCbzBDekk5bzBYQ3h2QUU2dnVIaGgwOUwwMXpFeW9hUkMxcmxnQ2JGcllPSDQ4ZVdQX0E1T045OFZDNnpTVlRPd0g3aXl0U0tTbFNPcTBNdWVYVF90YVFUdW50NnhST0ZWcEFFbHE0Rkh4VzVIeTFoLWg3QWVJQkkyVmlBVklmTUlHTVJMVlBfTmp1WUpORGtJR09BUnVFeDM3S0prSkhLdzhQLUlxWXBB0gG4AUFVX3lxTE9KdklJb3BhZ1dPVlM2R3NSRW4tLXFLaTBkVmNqMDNJN2Z3ZXlhVW9rMmIteUZ1N2N2OXgxSlRDNTlaVjdtUHlsUjZkQVM1UFpIUmhtUGdoZ3BYWnNxTE5WaTc5ejlXWFdwTXlrenVUUmp0ajRRQ1VZNEc3Qy1WandTcktYU01iMy1pMTZEMEdmODhLOXNKdV80LVhTcVR2cjk2QTc5TnVPR2tSeTNsZjJ0dlJ2YnFGc2Y?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:43 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:43 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:08:43 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/political-pulse/election-commission-row-unites-bengal-rivals-tmc-cpm-10894328/ "HTTP/1.1 403 Forbidden"
09:08:43 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/political-pulse/election-commission-row-unites-bengal-rivals-tmc-cpm-10894328/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/political-pulse/election-commission-row-unites-bengal-rivals-tmc-cpm-10894328/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:08:43 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiqwFBVV95cUxQcnBsRk9WalNoYmdRZW44emU1SFNTU1pPalB5TUx2UXFLVnRFMkt0LWdIbEMtYWU4UTVrVEJ2SV9NTlI2SU01MHdfTTBQZVk3eG9IbVhHRXNxakh0OHNHTkkxYUJmZWRwYWFaQWN1aldnZUpsMDRMRmpGYUxXamxZN1QydHo4Z1lPelp5aXVPWjRKa1loUHhIQ2hWcFVoN1FhRzUySlNINzRRRk0?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:44 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:44 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.dw.com
09:08:45 INFO    httpx: HTTP Request: GET https://www.dw.com/en/india-news-new-delhi-islamabad-trade-accusations-at-un-general-assembly/live-79440869 "HTTP/1.1 200 OK"
09:08:45 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMikAFBVV95cUxPeXV6cjZYYlUyRzN1RzIwWlQzS25ncm9hTHFCbjBwYU94SFNzYW9UWlo3SWhTQ3hab1Rpbk5FNjlKb2RnU3dpamxhbWtpZG5JU0ExNmRFSmw5RHM1dlF5c1pqM2Jqd01DUnpfTTFYNGRMTzN4eklvOGptaktXU1k0QWlmZENnU3QzSE5ELTI3UE4?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:46 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:46 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.espn.in
09:08:46 INFO    httpx: HTTP Request: GET https://www.espn.in/espn/story/_/id/49986455/india-medals-asian-games-2026-live-tracker "HTTP/1.1 202 Accepted"
09:08:46 ERROR   trafilatura.utils: lxml parsing failed: Document is empty
09:08:46 ERROR   trafilatura.utils: lxml parser bytestring Document is empty
09:08:46 ERROR   trafilatura.core: empty HTML tree: None
09:08:46 WARNING trafilatura.core: discarding data: https://www.espn.in/espn/story/_/id/49986455/india-medals-asian-games-2026-live-tracker
09:08:46 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMixgFBVV95cUxQRjNOcTBnQ3k5ZTROUGJxMDgyU1ZQazVFSmd3OS1Jc0J4VkZxeEI5bFJyM0VKVzgxVHRlLTk3aGpCZUlQTk03V1Z1WnN3X2lUbE9DbENBS3R1S19RY2RnXzhRaEtYSkF6Zkd1MTJYaFQzTWhScHNNalNxcjR2amxzVTdMdXRJVlZkRjRSZGVrbXhPOVh6dzdaSDg4S3NpV1B4NGV2LTlFZldjS0I1YkYwdmlRckVnSG04OXNES2pGVFdQQWs2X0E?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:47 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:47 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.reuters.com
09:08:47 INFO    grounded.pipeline.scrape: [paywalled] skipped www.reuters.com (reuters_india)
09:08:47 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiowFBVV95cUxQQU5MZmY4Sm9feVBpbl9uR1o4UVZ5YUlfTklBU2NhMDRFYVB6NmdwUS14SEEyLXFNbmhQcHZndVdtbjVzakNtOHZFb0VjNWdjeTVXZkFFcWx0VGNuUGFSYlNMMVlIcjB3cXdwSmtoTC1MOU1IYVJPak9kNWdHc3pOSXdseVlDbDVTWnY4R1phZlZCdkM4X1d0YjNhVkh5Z083RVd30gGqAUFVX3lxTFBoM2dBQzNfTEtuZ25ON0RwRWdYdHRJOUJvQVN4RWU4MExmdFF3WWt3UFJ2WHowN3JxcTVEREtXaUVHVXk2emVvUzM4Y2szUU5xdk5FM01UU0dMZW10a1dvR3UyYjdOZTRqaGV5dFdlTFhaRnk3c2lDWW9jRU1kY29EUjRrYWtNMi1HZ1lBQ3R5Z0lKdHo4TXJ2bWY2WUhJa2J4bkRnTlczN2JR?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:48 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:48 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:08:48 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/cities/ahmedabad/ssg-hospital-vadodara-bribe-demand-probe-10893731/ "HTTP/1.1 403 Forbidden"
09:08:48 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/cities/ahmedabad/ssg-hospital-vadodara-bribe-demand-probe-10893731/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/cities/ahmedabad/ssg-hospital-vadodara-bribe-demand-probe-10893731/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:08:48 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiswFBVV95cUxOdmpwRXVWMEhGSTROY3NlblRjaGtjamF2TzVMbGJoc25CbHRlak1UUHRlbkFrQktLd3hDd1d1aDVUT1JNcmN2U0haRFotbjBkNGJLUjN4U1dyNDNvZzFGbnhIMEtlYVVZREV1UXV1TnNZSmdaa1JWREhoTXZ5WERzbVVOSmdya0FDbGNZYU8zNGdrb29oaG1JVnVMUElMMzNrVUZIdlZhQUtGWmVCbjhDQjFlWdIBugFBVV95cUxNQzVTM29jWTdreUdjRFd4LTVYQTZ1R3JDUFRFZEU4eXUtY2Yza3VWZ3pSTzVXZzR5UEk5R1diTjE1Vk9JalgxS2xndGRIdHUtYmVvaGMxV3FTWkg0M1h0M1Q2TUxTUW01VDFVeFpERUFWa1JkSG9UOUtwVDdLYUVhWHZYNlc5LUtScEdIbUtZVWg5WlVQcG1fZEtYN2drSUh0MDd1V2Q2MTlpSWV4RlRSVlozT1Y2Ujc1bGc?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:50 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:50 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:08:50 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/national/karnataka/left-parties-seek-removal-of-cec-halt-to-sir/article71509000.ece "HTTP/1.1 200 OK"
09:08:50 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMixwFBVV95cUxObU1ZYUtRbkx5d3dBdTk0TVR0UkZfdDMydjdZT1puRFJVaF9EVjBUTHRjUDhPTlBxYW1pZ0JZLVQ4ZldYeWNvUFdUUUoySmlhcy1MS0t6cTg0aWZiUmZSTjQ3Rm54eTItQVk3ZG1ncGF3OWZZckhRelNsd3NucU40ZEtXaFJDaVRtSmVRa3JlcFZZUG12c0Y5UWhWb25ZeVdnc0IwYS1aMEYyM3ZwU1Z0bm83TkZrUDJ1VjczZzEzbHNPMHhZYlVV0gHUAUFVX3lxTFBYWGZsLUNLWEtyWDFOc3p3cWtER1V5T1Q4TkZRUi0wSW1ielpWeW0wQWRYOGN4OFUyOHdSQk4wUm00SXdyRWgwVXRCRHpjY05HVVhQYjRWMXZnbzhUa1h1QnBkY2o5ZlZ3TzU3VTJRXzlFclg1aTF2bG12QkFKY25mMEpjZUl3c3dsZTV1RUlUQm1XRmJYNFl6bDJ1YllXcmpIaFFrY3R2WmY0TjVienM5ak1ybzZ1Q2dJLVRCaWJXY0VDeFZQbjFIZU1jVDJuaF9jazBo?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:51 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:51 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.newindianexpress.com
09:08:51 INFO    httpx: HTTP Request: GET https://www.newindianexpress.com/india/2026/Sep/26/a-regime-of-the-army-by-the-army-for-the-army-india-tears-into-pakistan-at-un "HTTP/1.1 200 OK"
09:08:51 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiWkFVX3lxTE9Ta2hDc2d1QVBGVmR3djFIZWpVZUxwcjRkcE9jQUNSMS00eFJWMGIzcVdXM1AzUDdyMXVDd1NfTkVhb3QzbUJMTFp5RzhJTk92eUN0ZDFjUTc5dw?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:52 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:52 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.rbi.org.in
09:08:53 INFO    httpx: HTTP Request: GET https://www.rbi.org.in/scripts/bs_viewmmo.aspx "HTTP/1.1 200 OK"
09:08:54 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi1AFBVV95cUxOM254R3Z3T2xoOGNuSzdhVmVFMHlBY0RhMnRsMTFDRDVldGJqTVFwb2sxLW1lUTdHaS1jUkFkTmxucElwdjY0blA1Z3JqN283R1oyMFZ0RzdpZU5XdDBjME1Od0xxblVfQ2t6ckZUVURfYTFLY0ZzTXN5bkpCemU1OExzcm9jNVA3cFcxaWZiMDRXS08tRWhBQzR5VW91bV9hQkU2Sk1TbF9DY2FUdHA0eDVtVXpXNWpieHBJakgxRThYcmE5TEJIOWIxVFRXdHZNQXpOSA?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:55 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:55 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.espn.in
09:08:55 INFO    httpx: HTTP Request: GET https://www.espn.in/espn/story/_/id/50026312/india-asian-games-2026-aichi-nagoya-full-schedule-medal-events-fixtures-september-26-saturday "HTTP/1.1 202 Accepted"
09:08:55 ERROR   trafilatura.utils: lxml parsing failed: Document is empty
09:08:55 ERROR   trafilatura.utils: lxml parser bytestring Document is empty
09:08:55 ERROR   trafilatura.core: empty HTML tree: None
09:08:55 WARNING trafilatura.core: discarding data: https://www.espn.in/espn/story/_/id/50026312/india-asian-games-2026-aichi-nagoya-full-schedule-medal-events-fixtures-september-26-saturday
09:08:55 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi2gFBVV95cUxOSjN5ZVh6ZFFmNmJWY3NmanhYUm9XVHJCTjJyck9nUVhSNlFmcG9TQm9hSDEyRjVOdHFrN3VhUDlQMGE5Q1J3Vmx0WXo0WmZjWTF2bmc3ckVSNXNNM3hXVEg2Y2F2bS0wS096SERSQmZJNmNJWVNZZmVnNzhyV3psVjlJVkxvN2Q3RG4xZjhuTkpvWnVVVjdaTWJmMy1URzJocXNhSk94SVJyMkFVMlpuQUFGYzladmpQVVVsNE9GcDVHRzJsT0xQbFJlUzg1RWhwYWJoaTdrSkhfQdIB4AFBVV95cUxPNmZROEExWUw2Qk5CaDJmemlEcVBRTnRxS1FkV052YkpGMEJLenI4Z3pxQlBCQmd0ZS1QTndKdXU2cjduV0dkNldtczhPVE5ia011Y051aVEyNU0xNmVNQ3VNRnQtUUktajBaRUoyaTlvQ1dyaGxOYlc3QllmdlhvMlpTSzFST08yVnVhT1dNNzhnTVE4Z29uODlCTDFiOFQ4TUFVYzZMNVRFLWFaTEJMcEJYY0tnT294cVBWZktiWVotWkdQVzJOSEcxaUhnSkVmTmdFUkh4SndPLVc2bExCcQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:56 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:56 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:08:56 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/national/west-bengal/hundreds-march-in-separate-rallies-against-cec-gyanesh-kumar-in-kolkata/article71508832.ece "HTTP/1.1 200 OK"
09:08:56 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMinAFBVV95cUxNZlFmLVpMZTR0RXQ1dzUtcEZPUWNRY2czNjFIOXpQRUp5N2FzWkRpVUlwT2JMdnhDUjhRTGdKaEpmNk04MTNRM3RuMmt2VXFIeFRwdFV3NjNYdHByb0JqUmVCVWlXcThnRzY4NlJxUUJvVjFYRUZoYWwzYlp6d3FLTU00OXI5a2V2VHZUWkR5bUxGMzJwYWpDYnBmdmHSAaMBQVVfeXFMUEpvQ3ZESWx6WVpqbWs4dXlhNk9Ob3BCTlJqeG5xYVJ4TF9DWEpUSXdHLXZ0VmpNa0xpZE5kM0RsMV9KQmZkR3oxV2dVNGg3c01YLUtacVpXdGQ4ZU5rT056VlNxLXJISEdLdFRWaEpyWVBkWWNNYlFFUlhROTBTUE9DSnpMYXhEcEh1VFZ1Um9sZ18xWTVaZUw3eGIwYlJfWGVlUQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:57 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:57 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:08:57 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/india/cec-gyanesh-kumar-youth-voter-events-postponed-10893273/ "HTTP/1.1 403 Forbidden"
09:08:57 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://indianexpress.com/article/india/cec-gyanesh-kumar-youth-voter-events-postponed-10893273/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/india/cec-gyanesh-kumar-youth-voter-events-postponed-10893273/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:08:57 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi8AFBVV95cUxQTzZITE5iUU02N2p3QTBNMmhXX1VoZ3pRQmRGX1NLMU0wTDhzUHhTLUk4cWhadkdaNDRYMjZERDZlTEQxRFJBbHpZR0dYX01QRTZfWUVsOFFXazFBSnFZTmhCZEZwcFNhZzJJb3ZGY0FOcmN3Mmw4b3VLSGsxOHV1UUE5UlRfZUx0eG5JMDFaRmhFckY4eFVyOUtBNUpUOVBLS3VUbUxlMzFCdnBvbnh3SHV4UjRuWDYwdk5saW5ZbFRwZ1c4dFNPTjh4VXV0TmozbkFLSVJUWXdlU1FDckR2SGZYSDF6ejdqY0ZOMEVxTkrSAfcBQVVfeXFMTldjV0pMdVIzLTgxenpRVm9oa21mdEMzQTNEb1U4LUVOb29LbmowMmljekRDNzI5MVBZREdncElzYVRuSkRBVV83dFhFSHFIMDNmRGtsa3VtcGZuZHlfcE9YTC1mYVB6a0dDOTVsUklSX2JjUGszbzg2YWZxLWRQbTZydlpSaWdzSk80dzRBYWRQa0xzWHQ1eV9nSTNhNlhESUxVclRTclk4NDNnRmFJbEtnTlhCZzFhcW1PZW02dVNtQ1VINVVkSDZ0YlpLNGxwODczY2pTV3V1OW15ZnR4VUJndmh6cXBrcUt4VzNTRUZxc3FnTFpSNA?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:08:58 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:08:58 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:08:58 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/national/bihar/bihar-congress-stages-protest-against-cec-gyanesh-kumar-police-use-water-cannons-to-halt-march/article71508757.ece "HTTP/1.1 200 OK"
09:08:58 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi-wFBVV95cUxPRTA1djNVbmllSDBONmxBQUJxelJRaXJTMWFOaGpMZTNxZXpPcWlLdnNaeHY3aUNHWWVZWWF6Q21WcHBoR1FnVzNWWkZOTEM3dE14SEtNN2RoV3ZROGVNM1A5aUF1YzViQVlQeTN6NWtkcnRlR0d2bGNmcktHVkdCY05SYkhSZFhwLWNHdGpBZEJ3Szh6V3FGVXlnR3U2VXM4OVRKS2I2NE9qUGx2VThRRXJGMzQyZmtwb0p6U0JBcmRBMndYS0FDd1B4MHVEaTVjS01tMVJoNGMxdU1TaWVJcGRCUjVBdU9qS2NQUHFTbVZ5RVRGWXg3R0hBSdIBgAJBVV95cUxNWW9QSE9FZXBCR3djMm5QMDVsUDZfekRhUmhGNHpPZHZMSHhFTnlXOGVpdnA3bEtIaFNodm5fYmN6dDlDWG9zcnBlZTRfYUlEdURhUlpnblAtVW1aNkdQN3JpWWdoaTNwdTh3QkwxMXJOYW01TmQ2b3dMRG9haVhYR3FGRGRoa2pYRUVlWFFYVVF5RVM4QV9MTDJkM010NmVnRHJQdnN3QWg1bEhES0xnWVVobHdSSUVsYWR4X1ZQQ0paUkt6Rkh0dnRBS2s1VmotZmNWY0RUdl9VcHJtbjNYRndENjY5dGV2YkNUU3RTUkhYMm93ODJqdVM5RGt6V1ly?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:00 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:00 INFO    grounded.pipeline.scrape: decoded Google News URL -> timesofindia.indiatimes.com
09:09:00 INFO    httpx: HTTP Request: GET https://timesofindia.indiatimes.com/sports/asian-games-2026/another-gold-for-india-womens-kabaddi-team-beats-iran-to-clinch-asian-games-title/articleshow/134497880.cms "HTTP/1.1 200 OK"
09:09:00 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMirwFBVV95cUxNTjZERTJXN3UzQWUxbXFXNUdUbjFjc3ZVUFBUMW9EWWN2VGlPUkxKMm4waDIzc0VFdngxc3lCX25IWU8tN2FjT0h0ZGg4a0NLeGJBa1BFbUpqUjh6REI3SERJb3AwakhqTzBPRzZWcVBpTjlGREZ1OEROVjkxakZ2Mmg1RVlXX2tFTFFPZ3BZdWhuSm5GRmktQUdpenhSYUxyVTVCTHpXUUZ0SFFoazZR0gG2AUFVX3lxTE5vZndCM2JWT2RydS1zWDFSaTVxeTZmeWlrTkpzcG43Rm4ybWNsa0l3aHFZUjhjUHpCclF4QmFiTTNRdjZMcGZjZHVyeklzQTgwUnVXay03X2M1Z2dTWTRlYTRoTU5TUnRFdVZpOVJKTlNfaEMzclJJeFdTVkFzRmU3RTA5eUFRMjFDR1diMUd1RUFDSW04TUlzQ1M0b3FieHNtNFFEVU9IOFFoal9aQlpHSUJ6TXZB?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:06 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/india/cec-gyanesh-kumar-youth-voter-events-postponed-10893273/ "HTTP/1.1 403 Forbidden"
09:09:06 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/india/cec-gyanesh-kumar-youth-voter-events-postponed-10893273/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/india/cec-gyanesh-kumar-youth-voter-events-postponed-10893273/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:09:06 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMirgFBVV95cUxPR2tmS2Z0aEJTSTliN2VaV1JoWjU3eXBGdHFDR1Z4VTVZbkZuMUtSVVRsT1pBTElrUHJEaHhYVS1GMGxHeE9LeTZGTnR1SkZmVV9wRzNNVTNqa04wT2c5QmM4OHIyN2I2NldVTjV5dXJaeHJFTkxURmJTc3V6M2cyQTluc0loMVpMMDAzN1lFdWUwRUtGSXpDems3SDdfM2FPRUFUNXFnUTMtNERZYnfSAbQBQVVfeXFMT1A1QUx2elNlakR4MzlVRWFRMlZUZWJmVGdwR0lLTjZ3Q2VwRkZObVlGMWcwZW1pakd5YW42ZDAtNllJci16RWFvQk5fLVpOZjVFdVllSXpIdWNRU0NFdUtsenQzYTNMVUxhOHVMTDNJTkZ0ZVVSNHpBc2ZnN0JWZ0tfRHVIOHR2ams2S3BKNGw0MURZMEcwREJYMjdkRDRqWnlrQjIwQlZ0dnJxZHN1MG9nSGJy?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:07 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:07 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:09:07 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/national/karnataka/cpim-l-liberation-demands-removal-of-cec/article71508341.ece "HTTP/1.1 200 OK"
09:09:07 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi-wFBVV95cUxQWUJ3UDc5NmMyV3dvd2JGWVlYbEJkVkFCbHpWYmFVV080Rm9fU1lMWURoWThlSDhFUERwc3pxV1dyckZyYWF2WmkzN0hRMXMtcW9YdmRlbk1TQ3U4a2NtZDBLWlM1VlVubFhzeXE4Y3ZaMFFmWElVb2pnTFo0dkpVQlFFT2xJcndrdFgtNDFxYU9vd0VxbUh4Q0xGLXhHUGF6cXRNcWVtWXIyUVlrUXFub1hqc3B5azg3ODFHR1FWNTVvWmRrTWxDa1pJWjJJc1M2dGNpTEdNNjlkUUNSSjZHVjk3RGJMdkJpX1Zqc1huYkYwajZVVWxfUG9ia9IBggJBVV95cUxNdzhNWk1NSW9waW4tcUZmdWFRdUh3M0ExaHFnM0h6MGJGSEZtTzBwYV9RNmQwUnRzaUd3eWdYY2Uzb25sTjFUY3FtcGFLZFlyWUVwY2ZGZjFFY2c5bTZLTHNLUVhyTHhBWWdjejdDSVp2YTRSTi1hYWdUczkycjI0MWVTZDREQXUzMWpvYXB3bWxPVDM0LTZ0V2lDcEMwSXQwNDM4TW0za2JMOWdQeERUSEMxSXhMUlhVZFdybTR4cnZXNWtRSG9vQXVtbXhyZXZPX3UyUFVUdmNnV2xhM29YaXBJek83VUlIb21CLWhhcjcycnd4TGhWTG0wRl8yVEt2SFE?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:08 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:08 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:09:09 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/national/odisha/patnaik-blames-odisha-bjp-mps-for-mines-law-passage-in-parliament-warns-of-revenue-loss-for-the-state/article71508149.ece "HTTP/1.1 200 OK"
09:09:09 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMizgFBVV95cUxPZXJEc25ic3U4RkNiOF9EWmgzampWUnNIeGtUUFdPZm9jdDY4UmdUWVBlcEktS0lVUGNHSzhMSk1HTVYtVnFnLS1kWE1VcUxXSlRQc3ZDRHBPcXA4dk1DQi0yR0JVdFlUajdONDFSb0FEemtUM3laNWVLRTJoaW5ITnVrMENldTUzNi0xM2drWk5FdmhFV0o0cDRLSXNTZFRaSFZCQlFfQ3F2ejZ5VDA1U1NXb1phN01scW5nc2E1X3ZwM2pkZzg2Ty15aGRrQdIB1AFBVV95cUxQand3b05IenlWZUl1Z2Ftem14aUpYYWFtV0pnaGZRSEVZdHNlX0daVUl3Y0ROWE41ZFN4S0N0S0N2RlBWNDg3dS1GMDg4WlJpSHZCOS1LSFZhT1huNEhWU0Mta09td2RhZFJ6Wk40S2hhTE5qZ0YwQnIxUG1HME55V0NrdmJwZ2pnNEJ2TS1nZHVrblIwYjB3LWFKSDhjVWVScUtSZlZucG9malR5a1lQZkVVeFlGSXhHcEdpVGVoRE9SX1l3b0Jfd0VYUzUxanhseEstbA?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:10 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:10 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:09:11 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/national/gaurav-gogoi-detained-during-assam-congress-protest-demanding-cecs-removal/article71507995.ece "HTTP/1.1 200 OK"
09:09:11 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi0wFBVV95cUxPS1NuNE9OT2FOdmgzX0VHODItanpxYzNoczZZdHlsOFgzR1Rxd0FzdWw4VjNmSE03azBFaERBQjcycXJONnZvLWVLaUlKNTJ3eWpoX0hCa09zSWh5VU8tSDJkSFhNdE1zOHhPdFlGaWRNb3lUSy1ZQjhERllOd1J1bzNqYmk4eUlnUGNvUmhMRUJBU29Cd1NqQW04Ul9MbnFnb1pWcGI3Ym5pUzRWMEhTM2piLTVkekRJUGRiYUhnTnlHZTJWU2p2SWp4LVo0Y19ScVVB0gHYAUFVX3lxTE9ONE96U2MwOHBiU0xQcExaTWZoZVgwQ2F1N296NWdqeHVGaVktaHd2dVBXcmlkMzBJM0swUTk4LUxuZEZkTEtqU0RzVUN1VTNFd2p3S282ekZXbjZxeGI0ZWlzeGJVLVN5M1VacVZqLUdKcU4tNkdzczNMcDRiSndNYU1DOWkwY09xbWc3MUdka1AtWl96MGJYV3lZNUF6MTlwZVgxenhCVlg4TngwRzR2YjhfZmJwRUc4dWRZYXlUQjhIblBNMHJlR0luaGdST3dlZ1FYbXo3dw?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:12 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:12 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.indiatoday.in
09:09:12 INFO    httpx: HTTP Request: GET https://www.indiatoday.in/world/story/india-pakistan-unga-india-calls-pakistan-puppet-regime-warns-over-terrorism-ptag-3003329-2026-09-26 "HTTP/1.1 200 OK"
09:09:12 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMixgFBVV95cUxPVXJ4N19IRF85dEhIVjh3SnZhUl85M1l4aVI2aG1HWUh0V21WdHA2R3J4eXRScXpzQmJJcnVsaVJ5VmlrM08xaXU0XzJJTHBYUS1IQWRTQkdMd3IwMXJfcGJMQzlPOVJ2VUtmY1F3dUxnd3J2VUhfQ0FtRE11RG43UjRDcUpWSFBEYkhoWV9vMnVCb3pCSTJ1Sy01eGhacGdwYWJUa01uRHlKRmoxMzMtbHYtS1JBM3FDSktXcGJ5MnRQa0xrOGc?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:13 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:13 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.aninews.in
09:09:14 INFO    httpx: HTTP Request: GET https://www.aninews.in/news/sports/others/india-women-retain-asian-games-kabaddi-gold-beat-iran-37-34-in-thriller20260926104940 "HTTP/1.1 301 Moved Permanently"
09:09:14 INFO    httpx: HTTP Request: GET https://www.aninews.in/news/sports/others/india-women-retain-asian-games-kabaddi-gold-beat-iran-37-34-in-thriller20260926104940/ "HTTP/1.1 200 OK"
09:09:14 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMimAFBVV95cUxNeXpjVUE3SDhOUGpJMUtob0p0RFJtYV9iNDQtUEItVkgyWFI1V1hKUTVDSGNFZDJGSVhlUUQ4MjdUQlBQTk5QNXRLQ2l2UzJ1a2Y2NlZxMUpPOUYxc3JHTWlkcHJpT0RNazlOZS1VRll0MTJkQk1VdnFjUFdPSXBZdnkxZzJieXN3cjRHSFkxQzliaFZQSHpUYQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:15 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:15 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.olympics.com
09:09:40 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://www.olympics.com/en/news/asian-games-2026-shooting-india-scores-results-medal-winners: The read operation timed out
09:09:40 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiwAFBVV95cUxPR0J3eXdnbHpGVW5tWWlnTmkxcVhxdkhZMDBmd0VFSjRXNlJqTThOTDVUb3BodTlfZnVPRXRIZTVWQTVPX3JOWEFIc0hQZE4tNkZVWTRuRmRIVUsxQnFUS2tUQ2J0YktPS3o4ZjZ6UWpvbnQtRDBmOVJWcFlCYm5sc0FsLWVPdGprMnRJMjdkZVVNTF9nN2NjVVd5RG9ZcFoyVUFYVFE2UlFNajctM3RKZXpfWU1pN21Xb0tlRlhpSm3SAccBQVVfeXFMTzZsb0tQeGJGNW9CRk1GUEtrbThKR0V5VWU2eWJGUmhsMDhja2N2NF9BV2JJSEI2OHdGTUkzMXJMVHpIYXgtekJjc1FCSENqamNOOURoajl4U3pPZlNpdHM1N0VJdzFpZmVXc1lHQ2MtYXJFOEVVaDlHMEVTc3A3OXEwY2JqUEtPYTRWYmxYMHd4MjQyVXVGbFowNzFyS0ZjRWNfa3NSeWdwZThWM1B4VF9pOWZzbm5mUU9pcE1zNzFxdm5ZUjRMcw?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:41 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:41 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:09:41 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/national/kerala/pinarayi-calls-for-removal-of-gyanesh-kumar-from-cec-post/article71508635.ece "HTTP/1.1 200 OK"
09:09:41 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi1gFBVV95cUxPRW5aWl9OQk5uekIyNUxiR1FUS1V4REhsdWx6Z19qdl9KREpwVkdrMlpCTjVweGVoaXBhejNaVVBSRnlTOXp4QlY1S3NneHdaRFJSLVg2b052VjBITFprRUFqaTFVX2N5X1JmYnN1NWFVbzVzRExwUmMyV0ZLZ1ZQS09rWC1FTW1QNUZOM05hemxjTWRIczFBazBaUS03eUMtNUl6NnAwR1ROMVdzVXZSWnVveGpJNDE4aHpXb3N0M3Z1ZUtndFlZenVXbTU2Zm9rUG03MkhB0gHcAUFVX3lxTE1FZjBNMnVUVkxtV1RLSzZwZ29iRmx4ZjdSd2lQTk9YZkUzeER6N201VXdsUWdYRWdUb3hPZWxBT1F3NzF1QWxQdk5vZ1VJMUp0OG5TMEU3c2ptTUdmakVqczZMVHhNaEc4R2k0UEs3Z0lib1UwT0JNYjJ1emVQMFF4bFhMU3NKNWFYSFQ4Q3lseXF6STVwWlFqVTJ6MHdkUU53N3doWGdsMnpnM2hIeHRvU010ck1rUjc2YUZDNGg4TlE0VDIzaWtWaFMtVXJ0UThZWVFEcE5wakhJQmc?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:43 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:43 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:09:43 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/national/andhra-pradesh/left-parties-seek-gyanesh-kumars-removal-as-cec-suspension-of-sir/article71508315.ece "HTTP/1.1 200 OK"
09:09:43 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMic0FVX3lxTE5oX3Q2eTBpXzlvZVNwckJuaXJGOXFpYjRCZGxPSVRuTFNYb0VrX002ZVdVN2x4Y1B4QUNMeVpqdjd5N09seEF1cmxFX3N4anY4Tm16NDJEMlBMUlNGbVUyNHhEa0UzN1NQaGRaTnVCZF9PejQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:45 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:45 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.rbi.org.in
09:09:45 INFO    httpx: HTTP Request: GET https://www.rbi.org.in/Scripts/BS_ViewBulletin.aspx?yr=2026&mon=9 "HTTP/1.1 200 OK"
09:09:46 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiowFBVV95cUxPQVhScWxBM01nWm1qNjhJSXkyRW5LOGxEUmRtbFk0d28tUkdYRmVEYndVYzZiU01xaW5jMFM5eWpZcmdaNHlSN2RmX295MmhDQV9RZG01Q29fTG9SWWQ5R0xTU2ZoRHB5WHFoOEdzejlsZHV1b3FhUG5SaTZHNHJHc1NiZ3o4U1RHcHVrUzNNSmhoZWZQSDNLWXgxSkFCcEZqaU9j0gGqAUFVX3lxTE5sMjd6WTl4WWJRMDE5X3FvZ1NVVV9sZUNFUWx2NFlBYXpJQy1kaXlDSzZ0QkhFbXRiQWVMTGlhMzhSNi1SSTJhNVFLTWZ2S3BBQWxiaWR4UDdueGpGcXpHN0t2Q3BBdW0wYk1sU3pDUmd3ZkQ2X05vdWZIS3IySFJpa2J2SEJzcjd2OXhNS2VuNnZTVGlFbkU5YkhtVHFQajJNUHUxaDg0NlN3?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:47 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:47 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:09:47 INFO    httpx: HTTP Request: GET https://www.thehindu.com/sport/asian-games-2026-indias-women-roar-to-kabaddi-gold/article71511803.ece "HTTP/1.1 200 OK"
09:09:47 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi9wFBVV95cUxNZUlFdmhuODlqV3ZLZTdYZUtnSWtHR0JaX0VHLUVwTGliS3lna0hCZnVkQS13YUx0dTVIVkZFSVlMbTl5bEhXdmUwdkI4OTUxNnZfVUFCb2VpbXd1akJrWjVJaE9pUWhGWDFjbzB0QlRCbW5IREczeTJHLTRxT2dvYWtRaF9DZUhtcTJ1SzFNWER1ckRoZXZzOGhPbVQzd185S2FLbnBXSWo4bWNsUDBfZjJzUjJFc0JuYnBnN0JwQmNnUnpRQnc1aEdLM3ZPekFhNXNTOGxVMmptbFZmaDVDYXJvb21XcUtRdEVRUkVuUUxVQ2F6emh30gH8AUFVX3lxTE90ay1iNFFhZS1sS2dBNFNxdmhUTTVSNFMxTkpwamZvRmlRZEpaV3gxQTNUS3VIeG42eDNOMVFKUFNXM2Y4MmpiczEzSWs4dnd5YzlucVhRYUlWRXV6eGk2elVtSEU5cV8tdHdMNE5Dc2xWWDRiRmZwejZLVkFlZno3SVhBSXFhVWwzQmFRMDlkWXc5QmFOaUx5aHBZdDNrTkVLT3AyVzhpaVJXTU85aDVxdVB0dkFwemRTN3M3QmtkQTBoU3o2MkVxVndYSEhrb2hFWHZBelFwYXRYTUgtR1ZCWmtWaVZWbTJYd2RUamhQdHYtbjRNTnRJODctWg?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:48 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:48 INFO    grounded.pipeline.scrape: decoded Google News URL -> timesofindia.indiatimes.com
09:09:48 INFO    httpx: HTTP Request: GET https://timesofindia.indiatimes.com/sports/asian-games-2026/asian-games-2026-medal-tally-today-26/09/2026-india-rank-and-full-medals-table/articleshow/134497395.cms "HTTP/1.1 200 OK"
09:09:48 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMilwFBVV95cUxOZmVGTjNibnBsbXE5MmxUSkNTZjc4QVRocHk5SjN0OVhxLVRpTHJSOWJlc1dxc1RPOVd4SkdTY2NnUG1GcTB5SVJSdFJQUUtuWWhsTnJLYlE5cVdnaFd6S0ZfTHpuZGRxQlVHeWxoVFNsNE9yV2dUNTh5ZmVvcEN1SmdCaWctMmFuODFlVXF4ZjlOa1IxVjlz?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:09:49 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:09:49 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.olympics.com
09:10:15 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://www.olympics.com/en/news/asian-games-2026-india-schedule-today-september-26-saturday: The read operation timed out
09:10:15 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMirwFBVV95cUxPTzl5WThEME9zb0pWRVV5ZW0tUnBxOEI1RkhpTHFGQVJNVE9oNTctR2tZTXlBRUF4UDJCOEdWcTVvTTZ2aXpDUlRMdGswSlRCRGJIZ1REZDZuWDlXRGVwQjM4RjhTckZxNmFsZ2tKRktDQUZ3emJ1LU1zOGJnYlQ3bTVGSjlETms1TWhBcExqQlRxRjhFaHdPbTV1aDlYdjIyQWN6R0FvZXRKd1d1aFFN?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:10:16 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:10:16 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.olympics.com
09:10:41 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://www.olympics.com/en/news/asian-games-2026-kabaddi-final-india-vs-iran-live-streaming-telecast-schedule: The read operation timed out
09:10:41 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMieEFVX3lxTE80WUpkdkFGbTYzWE10NHgtM3JDV2RlVjduWVkzaTBHTkZoMGFlaWN0TFV6YW1oUmZ5VEMwVUVxd0dpYkxCVU9Od0RRZG9qS09EaHVGbTdVMWF4NDVxOFM4bnoxbFVVcDF6TkE5ZzZPRGRGQmxDaVRWSg?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:10:42 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:10:42 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.rbi.org.in
09:10:43 INFO    httpx: HTTP Request: GET https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63672 "HTTP/1.1 200 OK"
09:10:43 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiwgFBVV95cUxNcmNNZU5pVXBkTXhOVHJfVFZudHpVRXJXSEU2X2pkdW1FX3VvN2NOS25mOF9Rbk5uQUdUZlF6dWQ2djFlSjBCOExyZ0t5Umwyd2hoR3MwUVFFa0V1ZkNLU3E3cHdFdmRyZDd1SFpYV3p5STZ0NHRPWWY0YnBBYTZZWDJENXl2Q3p2WG9qMnhHQ2RXLWVRcng3NFlaTng2VHZ0b1dFMjhFUUVaWFVXNXluT2Y2c2xIZ3hKTkFDX1A5cUlid9IByAFBVV95cUxPYzIyNTB4eWljMGxYbDg3VlpiY0Z1V0lGWHo4akVWZnR1d2dUZTExVTFvc0xsTG1pcHY4UlluLUJLWlZ4VXBiMUQzd08xN1BWaHpBTzcwcEw1WFptQVJGclVYdUNWU3M3bVMyLU1KV1o1QWp2MzgxSHRybGltY1laWmVwMk54Qmc5WF84Z013b3RCdlNudE5PNFJrSUN4UGFPelg1dVY3NTdQWHBKTjZYZ0tRU2x2RUo5S0h6eC1LaEJHOGNNM2IzSA?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:10:44 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:10:44 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:10:44 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/political-pulse/exclusive-prashant-kishor-set-to-bring-jan-suraaj-party-to-delhi-10894300/ "HTTP/1.1 403 Forbidden"
09:10:44 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/political-pulse/exclusive-prashant-kishor-set-to-bring-jan-suraaj-party-to-delhi-10894300/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/political-pulse/exclusive-prashant-kishor-set-to-bring-jan-suraaj-party-to-delhi-10894300/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:10:45 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiWkFVX3lxTFBuUmM2eVBCYjZnS3A0N05CZHVQMWJ3aUxuM2pPSDlCUFNXaEczaXBpN2dNVE9nckpIdnFWUzhKVFRiR2F1eUhQZVQ3bU45UEJ1WXp1WXBxb2Mzdw?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:10:46 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:10:46 INFO    grounded.pipeline.scrape: decoded Google News URL -> rbi.org.in
09:10:47 INFO    httpx: HTTP Request: GET https://rbi.org.in/Scripts/BS_NSDPDisplay.aspx "HTTP/1.1 200 OK"
09:10:47 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMinAFBVV95cUxQZzRMWFV2V1NYWHhIdmxaTENrMFNyaWZUMzg0VnB4QVRwbEY3RjlTY1FxMmFuWjVmcGpKUmJqNnNFSUlhNXBvalJSeU5SZnVNck9NVXczeXowa3dDS0FoSmhzbGp2Vy1TT2NNbVJmNi1sbm42R2lwT28zM2h1S2liUXFOeWtjYXJrdFJmNDVWRkY0dDloT080aE5FZno?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:10:48 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:10:48 INFO    grounded.pipeline.scrape: decoded Google News URL -> ddnews.gov.in
09:10:49 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://ddnews.gov.in/en/asian-games-india-womens-kabaddi-team-clinches-gold-with-win-over-iran/: [Errno 104] Connection reset by peer
09:10:49 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMieEFVX3lxTFA1dlFWRndPZ1BwMDQ1alRiLVp3SVd5QTRIQzdGWEFXYm1qaWhFd09Ia281TWdqaC14MmlhT0U5WHh2cGI3aGhHUnBEZDU3X3Y1Q2dkZDdCS0JOa1JTeHRXYTZhTktVSnlZUW03ekcwOTN3UmxhX2ZFSA?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:10:50 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:10:50 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.rbi.org.in
09:10:51 INFO    httpx: HTTP Request: GET https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63668 "HTTP/1.1 200 OK"
09:10:51 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMidkFVX3lxTFBJb0lhVFlfVHVCTHdRaXlJVEREOGVDV0RNQlZqV3RTazIxNkJXSEtmWm9XNWY2YWQ0TlRJQWlfS01ZYWRTWkpJNVdHWEMybzV1SXRyT2JnaXl6aVFSVjZKWWJhdnowaTk5bEY3a2FvQk1lTXdzZlE?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:10:52 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:10:52 INFO    grounded.pipeline.scrape: decoded Google News URL -> m.rbi.org.in
09:10:53 INFO    httpx: HTTP Request: GET https://m.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63673 "HTTP/1.1 302 Found"
09:10:54 INFO    httpx: HTTP Request: GET https://rbi.org.in/ "HTTP/1.1 200 OK"
09:10:54 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMieEFVX3lxTE1KN095YUpBOWVNZkx2YkpNMHI0WFMxcE5CZVcwcXdmQ0c2SThTSTdHWDR6ZXVRdGNSa01uTnhJRGFGci1PWEVBWVhrSVNwc3Z4V0lsOC1sV1R2ZTJha2JVNTVSaXhIRDVzUnZtbDRua0hDUGxEZnUtLQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:10:55 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:10:55 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.rbi.org.in
09:10:57 INFO    httpx: HTTP Request: GET https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63667 "HTTP/1.1 200 OK"
09:10:57 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi1AFBVV95cUxOSVBhYmlCc1BnNmU2NDlrVlRoMy1Fd2FTcWIzclZ5ZmRXNjF6ZFpmeDh0ekZ6bWNZcTV2WmRUd1gzdEh0RUR4U0tjWXBfZUZLbXQzaUhZZXNEWkw5VmFWRGlDSHNJNklTTDJ0Sml6WHo5LUs2ZXMwaTRIRlpqQ0s5Ti1yMTBQOGR0SGtvR2p6aGVVZHo5YjZNbTlRRGFJZ1NpMmRCN25la3NzNGNvbWN0bXhPQ082NEF0aGR5Vm01QzZudk85TUlfcTlLUWNIRnJYNDZTSdIB2wFBVV95cUxOTndHbWFGU3BnLWpONTVtV3ZrNDZxYlVORlc3Z2lhNHJxcURBb0VWYThYYjBLQWRfZXN2d1BsSWdXOXJrSEN6RE0wdVZKLXN5dnhoV29wbnNoYlpvMVZJY0U0VlAzYW5mM3VOOUYySkFoOF9XOHFQT0JPX2o3dWdPek1mSHNqSUpfS3pfMEpKTlplVUZOaUh5Y2RpbFBFVmx5MUZrVTNJN2o4b2lLWklPd3FOdEpZcTZ2YnlNSjI2U2NhbFQ1RExXUTk3c3g5dE5LeDF5LVFFZS1xUjQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:10:58 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:10:58 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:10:58 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/entertainment/television/indian-idol-winner-abhijeet-sawant-recalls-teenage-struggle-in-mumbai-10893956/ "HTTP/1.1 403 Forbidden"
09:10:58 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/entertainment/television/indian-idol-winner-abhijeet-sawant-recalls-teenage-struggle-in-mumbai-10893956/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/entertainment/television/indian-idol-winner-abhijeet-sawant-recalls-teenage-struggle-in-mumbai-10893956/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:10:58 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMilgFBVV95cUxPeXYxLXF5NlJBcGtyZnBkVTZmUDdSZ2J6dEloV0YtSlNJTlVXY1BIQU1wR3VXUlRnRE9UekxWLVRrVWc1N1VoMlUydHFtUHhXOFU5VlliZUlMbkF6eDVwMjVxVWJseUgzd01YRV9IUUJEZkV0WjhkT0ttbUNQdHF4Y3FtSUs5MmFpZ1FUcTZqQmNpWXFBQXc?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:10:59 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:10:59 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.olympics.com
09:11:24 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://www.olympics.com/en/news/india-vs-panama-football-friendly-2026-result-score-report: The read operation timed out
09:11:24 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMijwFBVV95cUxOVXlVcmQ3dDlCaEs2VGxzYmJpajRXal95UmhwQmU3cjB4LWh5Z1hSQk5ZTXMyU2RsTjBrSXlxZWFkWE9RNzVLcm0xMXdvVGoxQjNWQ1lXeUU3ank5Vld0OUFydnAxT0VQMFpTcHlxR2VLdlk3cnBFblNyLU1VYkFCMlp5SDFkTjRsb0l1N1ZoRQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:11:25 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:11:25 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.olympics.com
09:11:51 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://www.olympics.com/en/news/asian-games-2026-medal-tally-india-winners-table-list: The read operation timed out
09:11:51 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMitAFBVV95cUxNdzRhalF6S2pIWVFyVjA1b3hpS1EtVVJ5Z1Y4R2dHbDJNVjdzTDYxMkJzeS0wNnRNQmpXNWgzZDBlUHZwa2s4cmhxM2hqR2l6NzU3a2NORUJmQVZTcEY1YWE1UE1CVWlOLWVicVBFWU1HVTRwOU5ablJFelpoNi1Vd0JTV0F2X0lwRURlSDFIdS1aWkxfS3BrSmk5c1RlZlI2T1ZMT1I0b2xRU0JWeWFtZldzNlQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:11:52 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:11:52 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.reuters.com
09:11:52 INFO    grounded.pipeline.scrape: [paywalled] skipped www.reuters.com (reuters_india)
09:11:52 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMisgFBVV95cUxNU291SEQ2QTNLWHlCOXVFXzhmM3gzYWJCaWlURENUWlg2ekdiZi1SS3ZwM2U2LXQ3LWNjVTg1R1Fobno0Sjg3cjd4ZGhYTk0xcFRkM1VNY1lfQWc4bUg1RzRDaVMycFViWUphWWs3aGUzRGl5RUsyZWVWVVA4M0NOb0hvQ3FYOVhiU25EXzg2R1JoN1h6dXJlSDhiYU9wU3FyM19zNmg5VUQtTzNOY2pkdVJB?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:11:53 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:11:53 INFO    grounded.pipeline.scrape: decoded Google News URL -> openthemagazine.com
09:11:53 INFO    httpx: HTTP Request: GET https://openthemagazine.com/india/terrorism-by-pakistan-will-have-consequences-india-hits-back-at-sharif-at-unga "HTTP/1.1 200 OK"
09:11:53 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiogFBVV95cUxNWE1NaW5kWGFudWxITUQtR1JjRlRyMDNkY2tsVFRuSGpGdDctc2tMZUhTZnVIdDBrelhjd0lCM2tKNm45RGxRVjFORkpPZlVYa2xQMlppZXM0d0V5cUtPUWwwX1dvNmk0Z2NrcTVadHZGYThncjVTTmlfa0pKa0NxN3lZSFJpTTM2N216OTNZUVlCWXIwbGU0ckhJTVlYRVh3VEE?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:11:54 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:11:54 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.ptcnews.tv
09:11:55 INFO    httpx: HTTP Request: GET https://www.ptcnews.tv/amp/nation/india-rips-into-pakistan-at-un-over-shehbaz-sharifs-speech-4429807 "HTTP/1.1 403 Forbidden"
09:11:55 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://www.ptcnews.tv/amp/nation/india-rips-into-pakistan-at-un-over-shehbaz-sharifs-speech-4429807: Client error '403 Forbidden' for url 'https://www.ptcnews.tv/amp/nation/india-rips-into-pakistan-at-un-over-shehbaz-sharifs-speech-4429807'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:11:55 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi6AFBVV95cUxPU3FGb1ViV3JZZUNRWDY1dmNaN05HakU0X0pSa3VsanBMb1U2UFA0enlGdjhsMVdxcDl0d0JoTE5hRTBxTjN0YjNTNWdQdkpzdW4yVWtCTTRzeUh0YlpIQkVyVjFfamxpUW1uaU44Q2hRR1dOaXE4T3dRdFlsdlRBNk16V2xYNWNFRjc5Z1pQWV9pYWgzZVZ6WE41RlB5eENjOVBSeTF2QkNXYTRiV2xhS2lRalhkSTM5QWFSZGFHaVRYaHlYcURObnE1UVIwLWZOTFNSa2EzcngtUy1xbmhpbTlIbnNYa3Iw?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:11:56 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:11:56 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.hindustantimes.com
09:11:56 INFO    httpx: HTTP Request: GET https://www.hindustantimes.com/sports/others/asian-games-2027-day-8-india-full-results-live-updates-marathon-kabaddi-shooting-squash-101790405350239.html "HTTP/1.1 200 OK"
09:11:56 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi5gFBVV95cUxOVnpET3MyZzZ6aGx2a191MjBTam1zTXdqa2hZLUdyc3p3dGhodF82blJSUnVKejJTblJEVm5NN0Z3X0tQTjVvQkhZQzl0ZEN0LWNWS2FWbWQ0SVNZQXhENEJPc3loVmpQTDVScnhoUmtqekl6X0gxR2hZVzl3Tk9JSDhzOGoyY0lKOXp6Z2hlVUYyZmVzNVZBRUZrblR5RFRERW1KaXdRSU5JQ09ORUFNVTJ0RE91ZlJsY0VtdWJrMFpRYnYwbFZkX05SQjVSQW44SlJCWlhJLVdrTW5QX2NsOHk1UzVFd9IB7AFBVV95cUxOTk5NVWlZRm9MOGxDcWJlSmI1d2dUcTNoZjFCZHE5ZnVidlRoQlg4WjdvemVXSzhOQ3B4MmFEZXZQSm8wRWhrSHgwTnhyTnd5NVhETzZ3WkFFN0dDeTlqUV9NaER3U1d3VFRqOEEzNktYZHh3dDl0d2RXaW5yck5VZ3pONFQxSm9TX3NGUFdOZ01Vcl80cDJQckRDOGhmbVpyeS02SjBTUGkyNmxqSURwS0JZZW9RcVJhZy1BdXNtQ0lHR2ZRUzE1VmhIZGgwckVlYmVSSGFfdmtSVzlZU3dkZU5mOW9OWGNsTkIyMg?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:11:58 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:11:58 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.thehindu.com
09:11:58 INFO    httpx: HTTP Request: GET https://www.thehindu.com/news/cities/Delhi/delhi-hc-directs-meta-to-immediately-remove-objectionable-morphed-photo-of-woman-with-pm/article71508478.ece "HTTP/1.1 200 OK"
09:11:58 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi7gFBVV95cUxOMUt0cFBVS2pHYzdNcndvaG1kTW44THBOaFhXdkRIZVB6TzNhb1JoSmZTOEUzbzd0S2dzOFVueG1Xay1HLU5peHp6UjVqUk50a3Q4V2tfV3ZFWDRTS3F3YjFBUFNyT0VxX29pMlFOaDBsa28wSVVhc25kU2l4Nk5nUXZ4R0oyamdEMGQzUnNZUERQeC15X2pCNjQ2MVNjRG1OSUZPTkxaZXREd183VTByeU56SVdnR3lIaVpkSWU3a1ZBYmFpQm80dnhaTUQ3U3pwOVl2bXdYNERXMENLTE9iSVZLdFM1UDlUbnI5a1R3?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:11:59 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:11:59 INFO    grounded.pipeline.scrape: decoded Google News URL -> sports.ndtv.com
09:11:59 INFO    httpx: HTTP Request: GET https://sports.ndtv.com/asian-games-2026/india-vs-iran-mens-kabaddi-final-free-live-streaming-asian-games-2026-live-telecast-when-and-where-to-watch-12100808 "HTTP/1.1 403 Forbidden"
09:11:59 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://sports.ndtv.com/asian-games-2026/india-vs-iran-mens-kabaddi-final-free-live-streaming-asian-games-2026-live-telecast-when-and-where-to-watch-12100808: Client error '403 Forbidden' for url 'https://sports.ndtv.com/asian-games-2026/india-vs-iran-mens-kabaddi-final-free-live-streaming-asian-games-2026-live-telecast-when-and-where-to-watch-12100808'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:11:59 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMigwJBVV95cUxONkdpV3F6UURZXzh2aE9WeURrU0V1bWNMM29XZnh4YmdFZkxtTzZsYUNSTmFvdy1lb3ZnU3dqZTRaN1RENTU1OVVVQ3h6S2hkOE81MUpaeWdaMUI5NG1ac2NOakdEOVdLMWpHRUw1Q3A2VTBqckFvcHhQVWJxM1lXWnFMZ2JVRFJBSHQ4Z3g1VWNpcnBzWGItQ0FEd3dsb0FIeUNmcjJFVnRqbFVBQlgzYUV4V3dDd2NUZV9PWThaY25hREgyVEN5SnRLYThVSG9IcW1GZ2w2cW85Q1B3R0h1d25ZbTFlcXlRbjhPdHNMbWFiTjJ6NV9oejRQUW1yeDUtLVRV0gGIAkFVX3lxTFBnU2tjWTdkUHhETDF6MDNHYkl6b3lPN1YzSDNIb3lQYWJpYV9sT09McGh4Q0owRENIWEdPbHpmVWFJTm5MRWFfTExxV3BjandkZEptQjlUQzdLajZOQ0gwSE1IQ3FfNXN2VW5zT0F0X0NienQycE9tMlBTU2ZPSXVJNFR2dEpEMWVYYlNGZDVPVm9ybGd2dThtLXFVbk9kNXhrejdNa3k3T3dRYVF1blBvbHZNYkJCQTFjZEJsdGpKSHVkOENQNXpHLXg1V1V1c0hoMFE0cUVNYlhtVVBIeEFWa1ZHUTluM01qMjZfWWZEUDdmckV1eUlDeUtUTUNKdWxEd3RtRFpPcQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:12:00 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:12:00 INFO    grounded.pipeline.scrape: decoded Google News URL -> timesofindia.indiatimes.com
09:12:00 INFO    httpx: HTTP Request: GET https://timesofindia.indiatimes.com/sports/asian-games-2026/asian-games-2026-india-medal-winners-full-list-of-athletes-and-medals-till-september-26/articleshow/134497843.cms "HTTP/1.1 200 OK"
09:12:00 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMid0FVX3lxTE5lRXV5OWFVd215b0VVN3BPVEZXdkY2RFVHeFdyajh6OHozbzFkdno1X2V1Sm9RRUhIQURNODZnemt6WnRidlpBLW9rV21ZUk9jaGt0ZUxCWkJySXJSQWJ6SXBpeG0xX3h1emlEc0V3TFRGWG96Mmcw?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:12:01 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:12:01 INFO    grounded.pipeline.scrape: decoded Google News URL -> m.rbi.org.in
09:12:02 INFO    httpx: HTTP Request: GET https://m.rbi.org.in/scripts/FS_PressRelease.aspx?prid=63664&fn=2757 "HTTP/1.1 302 Found"
09:12:03 INFO    httpx: HTTP Request: GET https://rbi.org.in/ "HTTP/1.1 200 OK"
09:12:04 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMidEFVX3lxTE1xbXVhamNDallWYWpJbUhtSlVld1BIek1qb1dNM2xCQTlrcEswQlAzTmpDQUJEYXJGRjBwTEhkbFJCSjlPaTFhVVBNeDhLUVRUc1FLTm50Q25yT0d3UzBMRGFKYVN4OEtSVlNWVkJsWElVOGx1?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:12:05 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:12:05 INFO    grounded.pipeline.scrape: decoded Google News URL -> vajiramandravi.com
09:12:05 INFO    httpx: HTTP Request: GET https://vajiramandravi.com/current-affairs/asian-games-2026-day-8/ "HTTP/1.1 200 OK"
09:12:05 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMieEFVX3lxTE9NYTNfZWR1LTNjcW1fY0J5dm5WS2dDNXZzNVVzUlJrQkdGUzNMcTEtUzhXRjlXRFF3VktKQkhSYVhfOUIzNjBOZVVKX3NGZVBrNlkwRGNTNm9mOTROdjk0VmZNX1QzQ1NhdXpjb0dWLThDRlJpcWtfUg?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:12:06 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:12:06 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.rbi.org.in
09:12:07 INFO    httpx: HTTP Request: GET https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63670 "HTTP/1.1 200 OK"
09:12:07 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi4gFBVV95cUxORjFDbHZsekNRNUIwTGNVRXZNV0I0eEVHdmxwc1dDYjNDX3I1TURYZzNzNEdNQm5MT0w1LWFBVVlqdVVqSTNoc215U0xmbmkxTkw2MzVjcXp3czhOVkFkemR3TnVMSkw1U1NBRUMtQ2o0aHBHTnp1TVNzVlRwSGxReGduRkNUcVZOWG9Ra1gteFhucVdBRTJ5REJIcC16YmU3T09pN2JfMFBCWnB5VEVWRi1tTnpJemNpV3R5aDFZSVJOODY5YXVVOUk2T3ROajVqYXBYRmY2dVV1WFQya0c2bnN30gHqAUFVX3lxTFBQaDNGaFcyTzZaUGNpQVdNeFRBYlM2ZHVGRDhuWEk2LUNLcWxaOV84bGpGZG9zOVlNeGRKdVFxcXJyaWNIWGxtWWx5Y1F5ZDJ3MThQNHprZE5qU3NoSUJJZzl2MWkxeTNkQU95cHo3TFZnUjYzTFFmS1ctcW5tS0ZkZWtoeGNtVVdpZjlkNGo0WWJoRXZrNUJBb3R1amRKTzl1NWZzTFBfUDBVcmF1NWYzT1ViWk1XUTJNZWRENmc3U1dnNUdKVFFXYl9ULUNnMmljNTlhOFZoa0xuR3B1aU9rdU9WeGFXbG1Jdw?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:12:08 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:12:08 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.ndtv.com
09:12:08 INFO    grounded.pipeline.scrape: [paywalled] skipped www.ndtv.com (google_news_india)
09:12:08 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMinAFBVV95cUxOalRYV2dwUDZGOExPWlFKVGhWUXhuMDZMckU1WUVGSVhULWpiSzdrblI4RzByYk1zZldiaEY3enpRRFlHZTdUdFZMd3UwRktib1huZ05iX3dPa1AxRGtROWd5S016cXhjYWg4bmx1NmxVRUVack95dzJWVWV1aUtsY25qOFVVUEJXRG94a0ZUd1U5blAwNERJaXhseTQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:12:10 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:12:10 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.olympics.com
09:12:35 WARNING grounded.pipeline.scrape: [google_news_india] fetch failed for https://www.olympics.com/en/news/asian-games-2026-live-scores-updates-results-india-september-26: The read operation timed out
09:12:35 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMitAFBVV95cUxNaEoyTlFJb3NOV1NUYTQ0ZGVENjVWS0RFY2x0Q3BLejdONzBtbHBETDRaZm5jQVB6dUpxVk5wdWx3el91MzFmMlcwVHFtWkktQVZ5dmgzUTByVTFFS3hrWHI3ZXdMa256OXd1TG9CUklxVGUzUXRQX2xFRXpVcUw2UFV2VkxaQ3lUTDg0eDNQc2VLMXFlb0I1NzJPWU1ud1JoUkJZZDl0WExTRUc0OEVETEVTbmnSAbsBQVVfeXFMTWlVMnRDZDlUQWFDTXFrT1ZDcnVBNENOMTJnZGlQWXVvdDQzZS1OUGZKc2dPYmJoQUkzVVNMUmVPSXFYUHpkRWN2TG9PUDlCSjVuUHBuUkwtbnhRWHhfX1VPYzA3d1JnT25ud2ZQblJnSE9wWHloZElVUFpWY0RiVDZTVmVEUjh3SW1ZVGZ3WnJPUTE5QXNieURCR2k5YTFzSENGTVM1SElhLVNva2d5YTVnaUs1TzNaSTdVTQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:12:36 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:12:36 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:12:36 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/sports/india-women-beat-iran-kabaddi-gold-asian-games-2026-medal-tally-10894689/ "HTTP/1.1 403 Forbidden"
09:12:36 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/sports/india-women-beat-iran-kabaddi-gold-asian-games-2026-medal-tally-10894689/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/sports/india-women-beat-iran-kabaddi-gold-asian-games-2026-medal-tally-10894689/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:12:36 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMirwFBVV95cUxQay0xM2dhV1JVQy14LVlCa0puYWhoeWhwYUlEZmdibjhRaVB6d2syMjhuejZ2RUxJelBLZmpHb0dYbjRMUF8xRGcyVzViTlc0dWsxMmZoWFJ2b1RDOFRtQmd0ZFRreVZ3d2I3dExSZlpFSGNpZkVQbzhKZEU4MExpRkJObk9DcUpXTE9OVXNUQ1cweHloa29YSmFka3pIcENlX1A2MFA4bFU0THRpT0xr0gG2AUFVX3lxTFAtcEZPWFRvbTBkQlVtc0VYSHhMRnVOT3V2UHZJdVNWMDhEcGhrRk5JTUdvSURzWm56aGdtWE9CWkUxQm52TDQ2T3U4elRFNW5wbDNvNk1HUFlzUzNaZmFFWkhRWm11alNuOWhVS0RMMnhnYVYwZ1hRYTk0eDh0Qm5rTU1QSGxGVEk2b0xVZHl3em9ma19tZG9FNUJJZFJRTTlrbFBRV01OYy1nNkxISHlYYWVqMmFB?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:12:37 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:12:37 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:12:38 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/sports/football/india-hold-panama-1-1-draw-in-fifa-friendly-result-10894207/ "HTTP/1.1 403 Forbidden"
09:12:38 WARNING grounded.pipeline.scrape: [indian_express] fetch failed for https://indianexpress.com/article/sports/football/india-hold-panama-1-1-draw-in-fifa-friendly-result-10894207/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/sports/football/india-hold-panama-1-1-draw-in-fifa-friendly-result-10894207/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:12:38 INFO    grounded.pipeline.scrape: scrape done: 45 with body, 3 empty, 30 fetch failure(s), 3 paywalled
  scraped 45, empty 3, failed 30 (of 81 pending)
[publish] building stories (crew)...
09:12:38 INFO    grounded.agents.runner: model routing: fact_extractor=nemotron, verifier=gemini, context=nemotron, perspective=nemotron, editor=gemini, reporter=nemotron, deduper=gemini
09:12:38 INFO    grounded.agents.runner: processing 25 candidate event(s)
09:12:38 INFO    grounded.agents.runner: === event 1/25 ===
09:12:38 INFO    grounded.agents.enrichment: event 5ee75b08-f789-4fd7-a767-9363d22d9070: attached 3 government-response doc(s)
09:12:39 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:12:39 INFO    grounded.agents.crew: event 5ee75b08-f789-4fd7-a767-9363d22d9070: building debate-mode story from 12 source(s) [primary=True] [EC postpones CEC Gyanesh Kumar’s youth outreach programmes -] — Political parties and protesters are demanding the removal of the CEC over the electoral roll revision, while the Election Commission and authorities are responding through postponements, police actio
09:12:39 INFO    grounded.agents.crew:   [1/5] fact extractor (nemotron)...
09:12:47 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:12:47 INFO    grounded.agents.fact_extractor: fact extractor (nemotron): 9 grounded claim(s)
09:12:47 INFO    grounded.agents.crew:   [2/5] verifier (gemini) on 9 claim(s)...
09:12:47 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:12:47 INFO    grounded.agents.crew:   [3/5] context (nemotron)...
09:12:49 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:12:49 INFO    grounded.agents.crew:   [4/5] perspective/debate (nemotron)...
09:12:50 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:12:53 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:12:56 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:12:58 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:12:59 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 503 Service Unavailable"
09:12:59 INFO    openai._base_client: Retrying request in 0.395735 seconds (retry 1 of 4)
09:13:01 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:04 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:04 INFO    grounded.agents.crew:   [5/5] editor/auditor (gemini)...
09:13:04 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:13:05 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:13:05 INFO    grounded.agents.crew:   -> APPROVED (8 claim(s) kept)
09:13:05 INFO    grounded.agents.runner: === event 2/25 ===
09:13:05 INFO    grounded.agents.enrichment: event e85b6e21-79cb-4fd3-bd76-236c630ca631: attached 3 government-response doc(s)
09:13:06 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:13:06 INFO    grounded.agents.crew: event e85b6e21-79cb-4fd3-bd76-236c630ca631: building debate-mode story from 14 source(s) [primary=True] [Shehbaz Sharif’s ‘act of war’ warning over Indus waters at U] — Pakistan and India trade accusations and counter-claims at the UN General Assembly over terrorism, Kashmir, and water issues.
09:13:06 INFO    grounded.agents.crew:   [1/5] fact extractor (nemotron)...
09:13:16 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:16 INFO    grounded.agents.fact_extractor: fact extractor (nemotron): 14 grounded claim(s)
09:13:16 INFO    grounded.agents.crew:   [2/5] verifier (gemini) on 14 claim(s)...
09:13:16 INFO    grounded.agents.crew:   [3/5] context (nemotron)...
09:13:17 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:17 INFO    grounded.agents.crew:   [4/5] perspective/debate (nemotron)...
09:13:18 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:20 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:26 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:26 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=did+the+World+Bank+issue+a+recent+statement+confirming+India%E2%80%99s+compliance+with+the+Indus+Waters+Treaty+during+the+2024-2025+period%3F+when%3A7d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
09:13:26 INFO    grounded.agents.research: research: no results for 'did the World Bank issue a recent statement confirming India’s compliance with the Indus Waters Treaty during the 2024-2025 period?'
09:13:32 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:34 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:37 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:37 INFO    grounded.agents.crew:   [5/5] editor/auditor (gemini)...
09:13:37 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:13:39 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:13:39 INFO    grounded.agents.crew:   -> APPROVED (7 claim(s) kept)
09:13:39 INFO    grounded.agents.runner: === event 3/25 ===
09:13:39 INFO    grounded.agents.enrichment: event 3f5bcfcd-d8c5-4bda-8abd-ed8e9766f818: attached 2 government-response doc(s)
09:13:39 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:13:39 INFO    grounded.agents.crew: event 3f5bcfcd-d8c5-4bda-8abd-ed8e9766f818: building report-mode story from 14 source(s) [primary=True] [India Women beat Iran for Kabaddi gold, country’s third in 2] — This is a straightforward sports news report about India winning the kabaddi gold medal at the Asian Games with no conflicting sides or debate.
09:13:39 INFO    grounded.agents.crew:   [1/5] fact extractor (nemotron)...
09:13:51 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:51 INFO    grounded.agents.fact_extractor: fact extractor (nemotron): 14 grounded claim(s)
09:13:51 INFO    grounded.agents.crew:   [2/5] verifier (gemini) on 14 claim(s)...
09:13:51 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:13:51 INFO    grounded.agents.crew:   [3/5] context (nemotron)...
09:13:52 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 503 Service Unavailable"
09:13:52 INFO    openai._base_client: Retrying request in 0.436948 seconds (retry 1 of 4)
09:13:53 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:53 INFO    grounded.agents.crew:   [4/5] perspective/debate (nemotron)...
09:13:54 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:13:56 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:14:00 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:14:01 INFO    httpx: HTTP Request: GET https://news.google.com/rss/search?q=what+was+the+margin+of+victory+in+the+India+vs+Iran+women%27s+kabaddi+final+at+the+2026+Asian+Games%3F+when%3A7d&hl=en-IN&gl=IN&ceid=IN%3Aen "HTTP/1.1 200 OK"
09:14:01 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMirwFBVV95cUxPTzl5WThEME9zb0pWRVV5ZW0tUnBxOEI1RkhpTHFGQVJNVE9oNTctR2tZTXlBRUF4UDJCOEdWcTVvTTZ2aXpDUlRMdGswSlRCRGJIZ1REZDZuWDlXRGVwQjM4RjhTckZxNmFsZ2tKRktDQUZ3emJ1LU1zOGJnYlQ3bTVGSjlETms1TWhBcExqQlRxRjhFaHdPbTV1aDlYdjIyQWN6R0FvZXRKd1d1aFFN?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:14:02 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:14:02 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.olympics.com
09:14:14 INFO    grounded.agents.research: research: fetch failed for https://www.olympics.com/en/news/asian-games-2026-kabaddi-final-india-vs-iran-live-streaming-telecast-schedule: The read operation timed out
09:14:14 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMimgFBVV95cUxQQmtDd2RZODlJcmlrRjhrcTBOeHA0UFR1VGVQTXVmblJObE1sMEg2MWRCd01BQ0kwXzBrUF9DVFFoa2xWT0poUWlDMWptSkVDNDdUc2Q2Qmp2VjRFdUk5MV95Q0oxakQ4UkJmR2pvb3pvaU01eEJ5TWxoOEpkZDRJalR6UFlNQXNDTXdRTkVNNG9NQWhnekZYSVRn?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:14:15 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:14:15 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.prokabaddi.com
09:14:16 INFO    httpx: HTTP Request: GET https://www.prokabaddi.com/features/asian-games-2026-kabaddi-day-3-live-updates-scores-results "HTTP/1.1 200 OK"
09:14:16 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMitAFBVV95cUxNaEoyTlFJb3NOV1NUYTQ0ZGVENjVWS0RFY2x0Q3BLejdONzBtbHBETDRaZm5jQVB6dUpxVk5wdWx3el91MzFmMlcwVHFtWkktQVZ5dmgzUTByVTFFS3hrWHI3ZXdMa256OXd1TG9CUklxVGUzUXRQX2xFRXpVcUw2UFV2VkxaQ3lUTDg0eDNQc2VLMXFlb0I1NzJPWU1ud1JoUkJZZDl0WExTRUc0OEVETEVTbmnSAbsBQVVfeXFMTWlVMnRDZDlUQWFDTXFrT1ZDcnVBNENOMTJnZGlQWXVvdDQzZS1OUGZKc2dPYmJoQUkzVVNMUmVPSXFYUHpkRWN2TG9PUDlCSjVuUHBuUkwtbnhRWHhfX1VPYzA3d1JnT25ud2ZQblJnSE9wWHloZElVUFpWY0RiVDZTVmVEUjh3SW1ZVGZ3WnJPUTE5QXNieURCR2k5YTFzSENGTVM1SElhLVNva2d5YTVnaUs1TzNaSTdVTQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:14:17 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:14:17 INFO    grounded.pipeline.scrape: decoded Google News URL -> indianexpress.com
09:14:18 INFO    httpx: HTTP Request: GET https://indianexpress.com/article/sports/india-women-beat-iran-kabaddi-gold-asian-games-2026-medal-tally-10894689/ "HTTP/1.1 403 Forbidden"
09:14:18 INFO    grounded.agents.research: research: fetch failed for https://indianexpress.com/article/sports/india-women-beat-iran-kabaddi-gold-asian-games-2026-medal-tally-10894689/: Client error '403 Forbidden' for url 'https://indianexpress.com/article/sports/india-women-beat-iran-kabaddi-gold-asian-games-2026-medal-tally-10894689/'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:14:18 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMi4wFBVV95cUxPMFVkU0NkbTQ5d3BHSnk5eXNNTnJoRVNOTENmdkRrQVhHZkNQalpmZEdseWUyUEJJa01KQndEaGF1N1NvNTMyU0U3c0R4MEIwZFdxaEY4a0plcHhiN2d6R2lYN3Faak1JTTFJdldPZGQtQndkTjlzd1pfRHBQZUJ2eEtMSTB4cHFFYS1SMFBqOHlfanhyc0xZeDJFSWFpdWViT3JjbjlMY29uM1B3dHdfVmRHNTVydlVlRnMtLWg4RlBuM3FqTUdEUmxmTllkSV83cnJvTXU3SVM3Z0JDVHAwS2VwSQ?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:14:19 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:14:19 INFO    grounded.pipeline.scrape: decoded Google News URL -> sports.ndtv.com
09:14:19 INFO    httpx: HTTP Request: GET https://sports.ndtv.com/asian-games-2026/india-vs-iran-live-streaming-asian-games-womens-kabaddi-final-live-telecast-when-and-where-to-watch-12100122 "HTTP/1.1 403 Forbidden"
09:14:19 INFO    grounded.agents.research: research: fetch failed for https://sports.ndtv.com/asian-games-2026/india-vs-iran-live-streaming-asian-games-womens-kabaddi-final-live-telecast-when-and-where-to-watch-12100122: Client error '403 Forbidden' for url 'https://sports.ndtv.com/asian-games-2026/india-vs-iran-live-streaming-asian-games-womens-kabaddi-final-live-telecast-when-and-where-to-watch-12100122'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403
09:14:19 INFO    httpx: HTTP Request: GET https://news.google.com/rss/articles/CBMiowFBVV95cUxNMEJUd1dQR3ROcncybTY5Yl91MWxtTW51dHhQXzVaOFl6N3BzYkJ5cDFneF92Y0dnT08zV3RRSXJmdjdBR01NbTdOUkExNG40aEVYQXVLRzlpZXc3aFBOcURKN01SUm4xN1YzV3ZOaTZDWnA2RUFKTjNlZ080OVpPazg1ajc3SXlDcHBwdHBnQXdfWE8zUUtJZWZRd0E0WVFySFFV?hl=en-US&gl=US&ceid=US%3Aen "HTTP/2 200 OK"
09:14:20 INFO    httpx: HTTP Request: POST https://news.google.com/_/DotsSplashUi/data/batchexecute "HTTP/2 200 OK"
09:14:20 INFO    grounded.pipeline.scrape: decoded Google News URL -> www.olympics.com
09:14:32 INFO    grounded.agents.research: research: fetch failed for https://www.olympics.com/en/news/asian-games-2026-kabaddi-scores-match-results-points-table-standings: The read operation timed out
09:14:32 INFO    grounded.agents.research: research: query="what was the margin of victory in the India vs Iran women's kabaddi final at the 2026 Asian Games?" → 1 doc(s) in 31613 ms
09:14:34 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:14:35 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:14:37 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:14:37 INFO    grounded.agents.crew:   [5/5] editor/auditor (gemini)...
09:14:38 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:14:39 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:14:39 INFO    grounded.agents.crew:   -> APPROVED (6 claim(s) kept)
09:14:39 INFO    grounded.agents.crew:   [+report] reporter (nemotron)...
09:14:48 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:14:48 INFO    grounded.agents.runner: === event 4/25 ===
09:14:48 INFO    grounded.agents.crew: event a7ad06db-7413-4a2b-b861-d32e031c995b: building report-mode story from 3 source(s) [primary=False] [India hold 44th ranked Panama to 1-1 draw in FIFA friendly -] — no substantive controversy signal (0 keyword hit(s))
09:14:48 INFO    grounded.agents.crew:   [1/5] fact extractor (nemotron)...
09:14:48 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 503 Service Unavailable"
09:14:48 INFO    openai._base_client: Retrying request in 0.381582 seconds (retry 1 of 4)
09:14:55 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:14:55 INFO    grounded.agents.fact_extractor: fact extractor (nemotron): 14 grounded claim(s)
09:14:55 INFO    grounded.agents.crew:   [2/5] verifier (gemini) on 14 claim(s)...
09:14:56 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:14:56 INFO    grounded.agents.crew:   [3/5] context (nemotron)...
09:15:00 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:00 INFO    grounded.agents.crew:   [4/5] perspective/debate (nemotron)...
09:15:00 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:02 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:06 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:07 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:10 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:11 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:11 INFO    grounded.agents.crew:   [5/5] editor/auditor (gemini)...
09:15:12 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:15:13 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:15:13 INFO    grounded.agents.crew:   -> APPROVED (14 claim(s) kept)
09:15:13 INFO    grounded.agents.crew:   [+report] reporter (nemotron)...
09:15:22 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:22 INFO    grounded.agents.runner: === event 5/25 ===
09:15:22 INFO    grounded.agents.enrichment: event 72938743-d206-4098-b261-02e8f2457d9b: attached 3 government-response doc(s)
09:15:23 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:15:23 INFO    grounded.agents.crew: event 72938743-d206-4098-b261-02e8f2457d9b: building report-mode story from 15 source(s) [primary=True] [India at Asian Games 2026 Day 8, September 26: Full schedule] — The event is a sports schedule and medal tally report with no opposing actors or controversy.
09:15:23 INFO    grounded.agents.crew:   [1/5] fact extractor (nemotron)...
09:15:36 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:36 INFO    grounded.agents.fact_extractor: fact extractor (nemotron): 14 grounded claim(s)
09:15:36 INFO    grounded.agents.crew:   [2/5] verifier (gemini) on 14 claim(s)...
09:15:36 INFO    grounded.agents.crew:   [3/5] context (nemotron)...
09:15:38 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:38 INFO    grounded.agents.crew:   [4/5] perspective/debate (nemotron)...
09:15:38 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:41 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:42 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:50 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:51 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:59 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:15:59 INFO    grounded.agents.crew:   [5/5] editor/auditor (gemini)...
09:16:00 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:16:00 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:16:00 INFO    grounded.agents.crew:   -> APPROVED (4 claim(s) kept)
09:16:00 INFO    grounded.agents.crew:   [+report] reporter (nemotron)...
09:16:03 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:16:03 INFO    grounded.agents.runner: === event 6/25 ===
09:16:03 INFO    grounded.agents.enrichment: event d58da5c7-4fe2-49cf-aa72-0a08d9195995: attached 1 government-response doc(s)
09:16:03 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:16:03 INFO    grounded.agents.crew: event d58da5c7-4fe2-49cf-aa72-0a08d9195995: building report-mode story from 3 source(s) [primary=True] [‘Concerns PM’: Meta gets 24 hours to drop morphed photo, CJP] — The event is a factual reporting of a Delhi High Court directive to Meta regarding a morphed photo, without opposing actors engaged in a debate.
09:16:03 INFO    grounded.agents.crew:   [1/5] fact extractor (nemotron)...
09:16:13 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:16:13 INFO    grounded.agents.fact_extractor: fact extractor (nemotron): 14 grounded claim(s)
09:16:13 INFO    grounded.agents.crew:   [2/5] verifier (gemini) on 14 claim(s)...
09:16:14 INFO    httpx2: HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions "HTTP/1.1 200 OK"
09:16:14 INFO    grounded.agents.crew:   [3/5] context (nemotron)...
09:16:15 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:16:15 INFO    grounded.agents.crew:   [4/5] perspective/debate (nemotron)...
09:16:15 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:16:16 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:16:21 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:16:23 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
09:16:35 INFO    httpx2: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
