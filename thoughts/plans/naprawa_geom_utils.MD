# Plan naprawy geom_utils (v2, po review)

## Cel

- Rozbic `eometadatatool/geom_utils.py` na kilka modulow bez rozwalenia API.
- Zmniejszyc zlozonosc i poprawic czytelnosc bez zmiany zachowania algorytmow.
- Utrzymac kompatybilnosc importow przez `eometadatatool/geom_utils.py` (facade).

## Kluczowe decyzje architektoniczne

1. **Bez nadmiernej fragmentacji**: docelowo 5 modulow, nie 9.
2. **Jeden modul antimeridian**: analiza + routing + splitting + pole detection + repair w jednym miejscu.
3. **Facade zostaje**: `geom_utils.py` re-eksportuje publiczne API przez caly okres migracji.
4. **Brak premature abstraction**: na tym etapie tylko `NormalizeConfig` i `SimplifyConfig`; bez `CrossingAnalysis`/`NormalizeResult`.
5. **Brak importow lokalnych**: zero importow wewnatrz funkcji/metod.

## Docelowy podzial modulow

```
eometadatatool/geometry/
  constants.py      # EPSILON, LON_MAX, LAT_MAX, HALF_EARTH_THRESHOLD
  projections.py    # wszystkie transformatory CRS i helpery projekcyjne
  antimeridian.py   # crossing analysis, pole routing, equator/AM split, repairs
  normalize.py      # normalize_geometry pipeline + clamp/orient/final validate
  simplify.py       # simplify_geometry

eometadatatool/geom_utils.py
  # facade kompatybilnosci: importy i re-export publicznego API
```

Uwagi:
- `average_angles` na start zostaje w `geom_utils.py` (zbyt mala funkcja, brak zysku z osobnego modulu).
- `_normalize_lon_to_360`, `lat_cross_antimeridian`, `lon_cross_equator` trafiaja do `antimeridian.py`.
- Nested closures (`is_pole_point`, `add_to_side`, `merge_paths`) beda podniesione do prywatnych helperow top-level w `antimeridian.py`.

## Baseline techniczny (stan obecny)

- Plik: `eometadatatool/geom_utils.py`
- LOC: 1182
- Liczba funkcji: 20
- Najwyzsza zlozonosc cyklomatyczna (radon, API):
  - `_split_at_antimeridian`: CC=25 (D)
  - `_rework_antimeridian_polygon`: CC=25 (D)
  - `_split_pole_routed_polygon`: CC=22 (D)
  - `normalize_geometry`: CC=22 (D)
  - `simplify_geometry`: CC=16 (C)

## Golden master - konkretna specyfikacja

### Dane wejsciowe

Zbior case'ow w `tests/fixtures/geometry/golden_inputs.json`:
- `synthetic`: przypadki z obecnych testow (`tests/test_geom_utils.py`),
- `real_world`: reprezentatywne footprinty Sentinel + MODIS + S5P (offline fixtures, bez runtime fetchy HTTP).

### Snapshot wyjsciowy

Plik `tests/fixtures/geometry/golden_expected.json` z polami per case:
- `case_id`
- `input_wkt`
- `expected_type` (`Polygon`/`MultiPolygon`)
- `expected_is_valid` (bool)
- `expected_bbox` ([minx, miny, maxx, maxy])
- `expected_area`

### Reguly porownania

- `type`: exact match
- `is_valid`: exact match
- `bbox`: abs diff <= 1e-6 dla kazdego elementu
- `area`: abs diff <= 1e-6 oraz rel diff <= 1e-6

### Cel

- Golden master ma blokowac subtelne regresje geometrii podczas refaktoru.

## Strategia testow (jawna)

1. **Testy API**: zostaja przeciwko `eometadatatool.geom_utils`.
2. **Testy algorytmiczne**: przenoszone do nowych plikow modulowych (`tests/geometry/test_antimeridian.py`, `tests/geometry/test_normalize.py`, `tests/geometry/test_simplify.py`).
3. **Migracja prywatnych testow**:
   - etap A: duplikacja (legacy + new) dla krytycznych przypadkow,
   - etap B: po uzyskaniu parity usuniecie testow zaleznych od prywatnych symboli z facade.

## Plan fazowy (5 faz)

### Faza 0 - Baseline i kontrakty

Zakres:
- Ustalic i zapisac golden master (input + expected + tolerancje).
- Zrobic baseline metryk (LOC, CC, czas krytycznych scenariuszy).
- Spisac kontrakt publicznego API facade (`normalize_geometry`, `simplify_geometry`, `average_angles`).

Gate wyjscia:
- `nix-shell --run 'uv run pytest tests/test_geom_utils.py -q'`
- `nix-shell --run 'uv run pytest -q'`
- `nix-shell --run "uvx --from radon python - <<'PY'
from pathlib import Path
from radon.complexity import cc_visit
src = Path('eometadatatool/geom_utils.py').read_text()
print(max(b.complexity for b in cc_visit(src)))
PY"`

### Faza 1 - Struktura pakietu i low-risk extraction

Zakres:
- Dodac `geometry/constants.py` i `geometry/projections.py`.
- Przeniesc stale i transformatory CRS (bez zmiany logiki).
- `geom_utils.py` importuje z nowych modulow i dalej eksportuje stare API.

Gate wyjscia:
- `nix-shell --run 'uv run pyright'`
- `nix-shell --run 'uv run pytest tests/test_geom_utils.py -q'`

### Faza 2 - antimeridian.py jako jeden pipeline domenowy

Zakres:
- Przeniesc do `geometry/antimeridian.py`:
  - `_normalize_lon_to_360`
  - `lat_cross_antimeridian`, `lon_cross_equator`
  - `_count_antimeridian_crossings`, `_detect_antimeridian_crossings`
  - `_insert_pole_points_at_crossings`
  - `check_contains_pole`
  - `_split_at_antimeridian`, `_split_polygon_at_equator`
  - `_repair_wide_quadrilateral`, `_fix_inverted_polygon`
  - `_split_pole_routed_polygon`
  - `_rework_antimeridian_polygon`
- Podniesc closures do helperow top-level z jawnymi argumentami.

Gate wyjscia:
- `nix-shell --run 'uv run pytest tests/test_geom_utils.py -q'`
- `nix-shell --run 'uv run pytest tests/geometry/test_antimeridian.py -q'`

### Faza 3 - normalize.py i simplify.py

Zakres:
- Wydzielic `normalize_geometry` do `geometry/normalize.py` jako jawny pipeline krokow.
- Wydzielic `simplify_geometry` do `geometry/simplify.py`.
- Dodac tylko 2 konfiguracje:
  - `NormalizeConfig` (progi clamp/validity)
  - `SimplifyConfig` (max_area_change, tolerance ranges, max_iter)
- Bez dodatkowych modeli, dopoki nie ma >1 konsumenta.

Gate wyjscia:
- `nix-shell --run 'uv run pyright'`
- `nix-shell --run 'uv run pytest -q'`

### Faza 4 - Stabilizacja, deprecacje i porzadki

Zakres:
- `geom_utils.py` zostaje cienkim facade i dokumentuje mapowanie starych symboli -> nowe moduly.
- Ograniczyc eksporty do publicznego API.
- Dodac check architektoniczny na import boundaries i brak importow lokalnych.
- Finalnie usunac duplikacje testow legacy, zostawic testy API + modulowe + golden master.

Gate wyjscia:
- `nix-shell --run 'uv run ruff check .'`
- `nix-shell --run 'uv run pytest -q'`
- `nix-shell --run "uvx --from radon python - <<'PY'
from pathlib import Path
from radon.complexity import cc_visit
src = Path('eometadatatool/geometry/antimeridian.py').read_text()
print(max(b.complexity for b in cc_visit(src)))
PY"`

## Co swiadomie usuwamy z poprzedniej wersji planu

- Osobne `splitters.py` i `repairs.py` (za duza fragmentacja, slabe granice).
- `models.py` z `CrossingAnalysis` i `NormalizeResult` (na razie niepotrzebne).
- Faza wydzielenia do osobnej publicznej biblioteki (przedwczesne dla domain-specific pipeline).

## Ryzyka i mitigacje

- Ryzyko: subtelna zmiana geometrii przy refaktorze.
  - Mitigacja: golden master + porownanie bbox/area/type/valid z tolerancja.
- Ryzyko: regresja wydajnosci dla S5P full-orbit.
  - Mitigacja: porownanie czasow baseline vs po kazdej fazie.
- Ryzyko: niekontrolowane API breaki.
  - Mitigacja: facade + testy API importujace tylko `eometadatatool.geom_utils`.

## Definition of Done

- `geom_utils.py` jest facade (bez ciezkiej logiki).
- Core pipeline siedzi w: `constants.py`, `projections.py`, `antimeridian.py`, `normalize.py`, `simplify.py`.
- Golden master przechodzi, a regresje Sentinel/MODIS/S5P sa zablokowane testami.
- Brak importow wewnatrz funkcji/metod.
- Wszystkie checki uruchamiane przez `nix-shell --run 'uv ...'`.
