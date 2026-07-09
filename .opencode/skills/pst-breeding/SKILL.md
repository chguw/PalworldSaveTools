# Breeding Formula — Development Notes

## Formula

**Simple average:** `child_rank = (parent1_rank + parent2_rank) // 2`

The result child is the breedable pal whose CombiRank is closest to this average.

## Tiebreaker (equidistant ranks)

When two breedable pals have CombiRanks equally distant from the computed average, the tie is broken by **parent rarity average**.

**Rule:** Pick the child whose rarity is closest to the average of the two parents' rarities. If still tied, pick the child with lower rarity.

**Rationale:** Verified against 3 in-game conflicting cases:

| Parent A | Parent B | Avg Rank | Contender 1 (rank/rarity) | Contender 2 (rank/rarity) | In-game result | Tiebreaker |
|---|---|---|---|---|---|---|
| Braloha (r8) | Dynamoff (r6) | 1215 | Quivern (1210/r7) | Azurobe Cryst (1220/r8) | **Quivern** | Rarity closer to parent avg (7 vs 8, parent avg=7) |
| Shaolong (r9) | Helzephyr Lux (r8) | 500 | Astegon (490/r9) | Dualith (510/r8) | **Dualith** | Rarity closer to parent avg (tie at 0.5), lower rarity wins (8 < 9) |
| Braloha (r8) | Jetragon (r20) | 550 | Univolt Cryst (540/r6) | Silvegis (560/r8) | **Silvegis** | Rarity closer to parent avg (6 vs 0, parent avg=14) |

**Key insight:** The child's rarity is matched against the parents' average rarity, not just picked arbitrarily. Legendary parents (high rarity) bias toward higher-rarity children.

## Verified Combinations

| Parent A | Parent B | Result | Source |
|---|---|---|---|
| Shaolong | Wumpo Botan | Eidrolon | In-game test |
| Shaolong | Orserk | Aegidron | In-game test |
| Shaolong | Helzephyr Lux | Dualith | In-game test |
| Shaolong | Petallia | Ghangler | In-game test |
| Braloha | Dynamoff | Quivern | In-game test |
| Braloha | Jetragon | Silvegis | In-game test |
| Braloha | Gobfin Ignis | Tarantriss | In-game test |
| Braloha | Beegarde | Beakon | Calculated (exact match) |
| Chikipi | Eye of Cthulhu | Chikipi | In-game test |
| Eye of Cthulhu | Braloha | Penking | Calculated |

## Data Flow

1. `update_game_data.py` reads `DT_PalMonsterParameter.json` from Exports
2. Extracts `CombiRank`, `Tribe`, `IgnoreCombi`, `Rarity` for each pal
3. Filters out unnamed pals and non-breedable (CombiRank ≤ 0)
4. Builds `rank_to_best` map from breedable pals (non-IgnoreCombi)
5. Computes formula results:
   - **breedable × breedable:** All pairs → `child_to_parents_formula`
   - **IgnoreCombi × all:** For IgnoreCombi parents with every partner → `parent_to_children_formula` and `child_to_parents_ignore`
   - **Unique combos:** From `DT_PalCombiUnique.json` → `unique_combos`, `child_to_parents_unique`
6. Saves to `resources/game_data/breedingdata.json`

## Changelog

| Date | Change | Reason |
|---|---|---|
| Initial | Weighted formula `(max*7+min)//9` from betatest script | Copied from external test tool |
| Fix 1 | Simple average `(r1+r2)//2` | Weighted formula gave wrong results (Shaolong+WumpoBotan→Anubis instead of Eidrolon) |
| Fix 2 | `parent_to_children_formula` added for IgnoreCombi parents | Orserk, Shaolong etc. showed no children |
| Fix 3 | `parent_to_children_formula` uses ALL pals as partners | IgnoreCombi×IgnoreCombi pairs missing |
| Fix 4 | `child_to_parents_ignore` reverse lookup added | Parents mode didn't show IgnoreCombi parents |
| Fix 5 | Rarity-based tiebreaker | Equidistant ranks gave wrong results; rarity matching parents' average fixed all 3 test cases |
| Fix 6 | Removed unconditional `best = p` bug | Extra line outside `if` block overrode rarity check |

## File Locations

- **Formula logic:** `scripts/scrs/update_game_data.py` → function `update_breeding_data()`
- **GUI tab:** `src/palworld_aio/ui/tabs/breeding_tab.py`
- **Breeding data:** `resources/game_data/breedingdata.json`
- **Exports source:** `Exports/Pal/Content/Pal/DataTable/Character/DT_PalMonsterParameter.json`
- **Unique combos:** `Exports/Pal/Content/Pal/DataTable/Character/DT_PalCombiUnique.json`
- **Pal names:** `Exports/Pal/Content/L10N/en/Pal/DataTable/Text/DT_PalNameText_Common.json`