# Credits & licences — SUS KIGALI HAIRCUT

Everything shipped in `sus/static/` is either the shop's own artwork or openly
licensed. Nothing is loaded from a third party at runtime.

## 1. Brand artwork (client-supplied)

| File | Origin |
|---|---|
| `img/logo.png` | Derived from `SUS logo.jpeg`, the shop's own logo, supplied by the client. |
| `img/logo-pole.png` | The barber-pole mark cropped from the same logo. |
| `img/favicon.ico`, `img/favicon-16.png`, `img/favicon-32.png`, `img/apple-touch-icon.png`, `img/icon-192.png`, `img/icon-512.png` | The barber-pole mark, cropped and re-scaled from the logo. |

The SUS Kigali Haircut logo and wordmark remain the property of the shop. They
are not covered by any open licence and must not be reused outside this project.

## 2. Web fonts

Both families are self-hosted in `sus/static/fonts/` (downloaded from the Google
Fonts CDN so the site makes no third-party requests) and both are licensed under
the **SIL Open Font License 1.1**, which permits commercial use, self-hosting,
and redistribution.

| Family | Designer / foundry | Files | Licence |
|---|---|---|---|
| **Fraunces** | Undercase Type (David Jonathan Ross) | `fraunces-100_900-normal.woff2` | SIL OFL 1.1 |
| **Manrope** | Mikhail Sharanda | `manrope-200_800-normal.woff2` | SIL OFL 1.1 |

- Fraunces — https://fonts.google.com/specimen/Fraunces
- Manrope — https://fonts.google.com/specimen/Manrope

## 3. Photographs

All photography comes from [Unsplash](https://unsplash.com) and is used under the
[Unsplash License](https://unsplash.com/license), which grants free commercial
and non-commercial use with no permission or payment required. Attribution is not
mandatory under that licence, but it is given here as a matter of good practice.

Each file was downloaded from the Unsplash CDN at the size listed below. The
`photo-…` string in the URL is Unsplash's permanent image identifier — searching
that identifier on unsplash.com resolves to the photographer's page.

| File in `sus/static/img/` | Unsplash image ID | Subject | Downloaded as |
|---|---|---|---|
| `hero.jpg` | `photo-1503951914875-452162b0f3f1` | Straight-razor shave in a low-lit barbershop | 2000 × 1200 |
| `chair.jpg` | `photo-1512690459411-b9245aed614b` | Vintage leather barber chair with brass fittings | 1400 × 1050 |
| `tools.jpg` | `photo-1517832606299-7ae9b720a186` | Barber tools laid out on a striped cape | 1400 × 933 |
| `salon-mono.jpg` | `photo-1560066984-138dadb4c035` | Monochrome salon interior | 1400 × 933 |
| `salon-bright.jpg` | `photo-1633681926022-84c23e8cb2d6` | Bright modern salon interior | 1400 × 933 |
| `fade.jpg` | `photo-1599351431202-1e0f0137899a` | Close fade cut finished with a comb | 1000 × 1250 |
| `clipper.jpg` | `photo-1622286342621-4bd786c2447c` | Clipper work on the back of the head | 1000 × 1250 |
| `styling.jpg` | `photo-1580618672591-eb180b1a973f` | Blow-dry styling with a round brush | 1000 × 1250 |
| `hair.jpg` | `photo-1522337360788-8b13dee7a37e` | Long hair braided and finished | 1000 × 1250 |
| `nails.jpg` | `photo-1604654894610-df63bc536371` | Freshly manicured nails | 1000 × 1000 |

To re-download or swap any of these, use the same CDN pattern:

```
https://images.unsplash.com/<image-id>?w=<width>&h=<height>&fit=crop&crop=<entropy|faces>&q=74&fm=jpg&auto=format
```

`crop=faces` is used for the portrait-orientation shots so the subject stays
centred when the image is cropped by `object-fit: cover` at different breakpoints.

## 4. Code

Application code, templates and CSS in this repository are original work written
for SUS KIGALI HAIRCUT. The three-colour rule used throughout the design system
(a red / gold / blue bar) is an abstracted visual reference to the barber pole —
no third-party icon set or UI framework is bundled.
