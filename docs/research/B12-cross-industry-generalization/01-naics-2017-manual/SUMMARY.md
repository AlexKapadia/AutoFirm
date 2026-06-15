# SUMMARY — NAICS United States 2017 Manual (the parameterization standard)

## Full citation
- **Title:** *North American Industry Classification System (NAICS), United States, 2017*
- **Authors/Org:** Executive Office of the President · Office of Management and Budget (OMB),
  Economic Classification Policy Committee (ECPC); jointly with Instituto Nacional de Estadística
  y Geografía (INEGI, Mexico) and Statistics Canada.
- **Year:** 2017
- **Venue/Publisher:** U.S. Government (OMB); distributed via U.S. Census Bureau.
- **URL:** https://www.naics.com/wp-content/uploads/2022/07/2017_NAICS_Manual.pdf
  (official mirror; primary at https://www.census.gov/naics)

## Ontology questions informed
- **L1.B12.2** — NAICS/GICS as a parameterization for playbooks (PRIMARY anchor).
- Supports **L1.B12.1** (the invariants question) by defining the production-process axis along
  which industries differ.

## GRADE tier
**High.** Official government statistical standard, jointly maintained by three national
statistical agencies (OMB/ECPC, INEGI, StatCan). No down-rate: it is the authoritative primary
artifact for the classification it defines. (Indirectness note: it is a *statistical* taxonomy,
not a *business-playbook* taxonomy — see BEST-PARTS for the implication.)

## Key claims with exact wording + locators (Introduction/Foreword, pp. 1-14)

1. **Single principle of aggregation - production-oriented.** Exact quote:
   > "NAICS is the first industry classification system that was developed in accordance with a
   > single principle of aggregation, the principle that producing units that use similar
   > production processes should be grouped together."

2. **Supply-based / production-oriented concept (why).** Exact quote:
   > "...production processes are classified in the same industry, and the lines drawn between
   > industries demarcate, to the extent practicable, differences in production processes. This
   > supply-based, or production-oriented, economic concept was adopted for NAICS because an
   > industry classification system is a framework for collecting and publishing information on
   > both inputs and outputs..."

3. **20 sectors.** Exact quote:
   > "NAICS divides the economy into 20 sectors. Industries within these sectors are grouped
   > according to the production criterion."

4. **Hierarchical digit structure (5 levels, 2-6 digits).** Per the official Census "Understanding
   NAICS" guidance (corroborating source 02), each digit adds detail:
   - 2-digit = **Sector**
   - 3-digit = **Subsector**
   - 4-digit = **Industry Group**
   - 5-digit = **NAICS Industry** (internationally comparable level)
   - 6-digit = **National Industry** (country-specific detail)

5. **International comparability at 5 digits; 6th digit national.** Exact quote (Introduction):
   > "In most sectors, NAICS provides for comparability at the industry (five-digit) level."
   The three countries "strive to create industries that do not cross two-digit boundaries of the
   United Nations' International Standard Industrial Classification (ISIC)." The 6th (national)
   digit is the level at which the US, Canada, and Mexico may diverge.

6. **Tri-national governance.** INEGI (Mexico), Statistics Canada, and U.S. OMB/ECPC "jointly
   updated the system of classification of economic activities that makes the industrial
   statistics produced in the three countries comparable." Revised on a ~5-year cycle (2017, 2022,
   2027...).

## Reproducibility note
Re-derive by fetching the PDF and reading the Foreword + Introduction; the production-principle
quote is in the introductory pages, the 20-sector and five-digit-comparability statements
immediately follow. The level naming is confirmed against the Census "Understanding NAICS" page
(source 02).
