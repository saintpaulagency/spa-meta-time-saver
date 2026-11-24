# SPA Ultimate Meta Time Saver

Saint Paul Agency's dashboard for checking and posting Meta ads.

The page (`index.html`) is locked: the app inside it is encrypted with the team
password (PBKDF2-SHA256, 600,000 rounds, AES-256-GCM). Only the lock screen and
logo can be read without it. The password is never stored in this repo.

## What it does

- **Today** – what needs a click across every live Meta ad.
- **Carousels** – every live carousel's cards as they are in Meta. Edit a card,
  swap a vehicle, add cards up to 10, then **Post to Meta**. Each post rebuilds
  the ad the house way (multi-advertiser off, the ad's other settings kept) and
  checks the result.
- **Setup check** – every live ad against the house setup (multi-advertiser off,
  Advantage+ creative and auto-enhancements off, carousel music off, UTMs,
  placements by format), with one-click fixes.
- **Monday → Meta** – each Meta line in the Monthly Launchpad next to the Meta
  campaigns it pays for, with budget and missing-campaign flags. Next-month
  drafts are only possible once a Monday line is confirmed with a budget, and
  only when someone clicks.
- **Log** – everything posted from that browser, with undo for ad edits.

Every change to Meta is shown and confirmed on screen first.

## Keys

Meta and Monday keys are pasted into **Keys** on the dashboard and stay in that
browser. They are never committed here.

## Building

```
DASH_PASSWORD=... python3 tools/pack.py unpack   # app source is kept locked in src.enc
DASH_PASSWORD=... python3 tools/build.py         # writes index.html
DASH_PASSWORD=... python3 tools/pack.py pack     # after editing the source
```

## Meta Targeting Map

`targeting-map/` is the Meta Targeting Map (every live campaign's location targeting drawn
around the client's stores), so the team can open it without Claude. It opens from the
**Open map** links in the Meta Location Targeting Tracker sheet. The page is encrypted with
a key that lives only in those links (the part after `k=`), so the repo holds nothing readable.

To publish a new version of the map:

```
MAP_KEY=<key from the sheet's Map links> python3 tools/targeting_map.py path/to/map.html
```

Without `MAP_KEY` the tool makes a new key; then update the two Map formulas in the sheet
('By client'!F2 and 'By campaign'!F2). Never commit the key.
