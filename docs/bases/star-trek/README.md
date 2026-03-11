# Star Trek TV Shows

**A hierarchical media catalog demonstrating multi-level aggregations and polymorphic ratings.**

This base models the Star Trek franchise as a three-tier hierarchy (Series → Seasons → Episodes) with a ratings system that can target either series or individual episodes.

---

## What This Base Demonstrates

- **Hierarchical relationships**: Series contain Seasons, Seasons contain Episodes
- **Multi-level aggregations**: Episode count rolls up to seasons, then to series
- **Polymorphic foreign keys**: Ratings can point to either Series OR Episodes
- **Conditional display logic**: Rating display adapts based on what's being rated
- **Boolean derivations**: `IsLongRunning` (>50 episodes), `IsGood` (rating >= 4.5)

---

## Entity Model

```
Series (TOS, TNG, DS9, VOY, ENT...)
    └── Seasons (many)
            └── Episodes (many)

Ratings
    ├── Series (optional FK)
    └── Episode (optional FK)
```

---

## Tables Overview

| Table | Key Fields | Calculated Fields |
|-------|------------|-------------------|
| **Series** | title, show_code, network, premiere_date | `name`, `total_seasons`, `total_episodes`, `is_long_running`, `rating`, `is_good` |
| **Seasons** | series, season_number, title | `name`, `show_title`, `show_network`, `episode_count`, `episodes` |
| **Episodes** | season, episode_number, director, writers | `name`, `season_number`, `season_title`, `season_description` |
| **Ratings** | rating (1-5), users_name, series OR episode | `name`, `display_name`, `series_name`, `episode_name` |

---

## Key Formulas

### Series Name (Concatenation)
```
Name = SeriesNumber & "-" & ShowCode
```
Generates: "1-TOS", "2-TNG", "3-DS9"

### Total Episodes (Multi-Level Aggregation)
```
TotalEpisodes = SUM(Seasons!EpisodeCount)
```
Sums episode counts across all seasons - a two-level rollup.

### Is Long Running (Boolean Derivation)
```
IsLongRunning = TotalEpisodes > 50
```

### Rating Display Name (Conditional Logic)
```
DisplayName = IF(Series = BLANK(),
    "Episode: " & EpisodeName,
    "Series: " & SeriesName)
```
Adapts the display based on whether this rating is for a series or episode.

### Episode Name (Zero-Padded)
```
Name = Season & "-Episode-" & IF(EpisodeNumber < 10, "0", "") & EpisodeNumber
```
Generates: "Season1-Episode-01", "Season1-Episode-12"

---

## Generated SQL Highlights

### Multi-Level Aggregation
```sql
CREATE OR REPLACE FUNCTION calc_series_total_episodes(p_serie_id TEXT)
RETURNS NUMERIC AS $$
BEGIN
  RETURN (
    SELECT COALESCE(SUM(calc_seasons_episode_count(season_id)), 0)
    FROM seasons
    WHERE series = p_serie_id
  );
END;
```

### Conditional Display Logic
```sql
CREATE OR REPLACE FUNCTION calc_ratings_display_name(p_rating_id TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN (
    CASE WHEN (SELECT series FROM ratings WHERE rating_id = p_rating_id) IS NULL
         THEN CONCAT('Episode: ', calc_ratings_episode_name(p_rating_id))
         ELSE CONCAT('Series: ', calc_ratings_series_name(p_rating_id))
    END
  )::text;
END;
```

### Function Composition
```sql
-- calc_ratings_name calls calc_ratings_display_name
CREATE OR REPLACE FUNCTION calc_ratings_name(p_rating_id TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN CONCAT(calc_ratings_display_name(p_rating_id), '-', users_name);
END;
```

---

## Complexity Profile

| Metric | Value |
|--------|-------|
| Tables | 7 (4 domain + 2 meta + 1 placeholder) |
| Relationships | 4 (hierarchical + polymorphic) |
| Calculated fields | 16 |
| Aggregation depth | 2 levels |
| Conditional formulas | 2 |
| Generated functions | 40+ |

---

## Design Patterns Demonstrated

### 1. Hierarchical Rollups
Episode counts aggregate to seasons, then seasons aggregate to series. The view presents `total_episodes` without requiring client-side summation.

### 2. Polymorphic References
Ratings can target either a Series or an Episode. The `display_name` field adapts accordingly - a common pattern for comments, attachments, or audit logs.

### 3. Lookup Denormalization
Episodes have `season_title` and `season_description` surfaced directly, avoiding JOINs at query time.

### 4. Boolean Flags
`is_long_running` and `is_good` are derived booleans that enable simple filtering: `WHERE is_long_running = TRUE`.

---

## Example Data Shape

```
Series: Star Trek: The Next Generation (2-TNG)
├── total_seasons: 7
├── total_episodes: 178
├── is_long_running: TRUE
├── rating: 4.8
└── is_good: TRUE

Season: 2-TNG-Season-3
├── show_title: Star Trek: The Next Generation
├── episode_count: 26
└── episodes: [list of episode IDs]

Episode: Season3-Episode-15 (Yesterday's Enterprise)
├── season_number: 3
├── season_title: Season 3
└── director: David Carson
```

---

## Why This Base Matters

This demonstrates real-world media catalog patterns:

1. **Streaming services** model content hierarchies the same way
2. **Polymorphic ratings** are common for reviews, comments, reactions
3. **Multi-level aggregations** are essential for dashboards and analytics
4. **Conditional display** handles mixed-type references gracefully

---

## Files in This Directory

- `effortless-rulebook.json` - Snapshot of the rulebook for this base
- `README.md` - This file

---

*Base ID: `appqwWQxIWFtyDsiL`*
