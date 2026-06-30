# Portfolio Project Brief: SKU Rationalization Framework

**Working title:** *"The 15 SKUs That Are Costing You More Than They Earn"*

**Repo (recommended):** `sku-rationalization`

**Status:** Brainstorm / Brief stage
**Tier:** 3 (valuable supporting piece — expands one Velocity Decision Tool module into a deep standalone framework)
**Priority:** After the all-tier diagnostic pieces (#195, #196, #198). Compounds directly with Velocity Decision Tool and Where the Money Actually Comes From.

---

### 1. The Pain

The founder launched with 5 SKUs. The brand now has 60. Nobody has killed one.

SKU proliferation is the silent margin destroyer at $10M–$30M specialty food brands. Each SKU accumulates cost that nobody totals up:

- **Slotting fees** — paid upfront, maintained annually. A SKU that sells 2 units/store/week still costs the same slotting fee as one that sells 20.
- **Trade spend** — allocated per SKU per retailer per promo period. The slow SKU gets the same trade spend obligation as the fast one.
- **Production complexity** — each SKU means a changeover at the co-packer. More SKUs = more changeovers = more downtime = higher effective COGS. A 90-SKU brand spends 15–25% of its co-packer capacity on changeovers.
- **Warehouse and inventory carrying cost** — each SKU occupies space, ties up working capital, and risks expiration.
- **Data maintenance** — each SKU needs item setup at every retailer, nutritional data in GDSN, labeling compliance, packaging artwork. Every attribute change multiplies by SKU count.
- **Management attention** — the ops team is managing 60 SKUs when 35 would run tighter, faster, and more profitably.
- **Cannibalization** — some SKUs steal sales from higher-margin siblings. The "Chipotle Lime" variant doesn't bring new buyers to the brand — it splits the "Original" buyer into two lower-velocity items, both now closer to the delisting threshold.

The brand keeps every SKU because:
- "We already paid the slotting fee" (sunk cost fallacy — the slotting is gone; the ongoing cost of maintaining the SKU isn't)
- "The buyer likes having the full line" (unverified assumption that often doesn't survive a direct conversation with the buyer)
- "It still sells a little" (ignoring that the full loaded cost of that "little" exceeds the contribution)
- "It was the founder's first product" (emotional attachment that has a dollar cost)

**Who feels it:**
- **$3M–$10M:** The founder. They launched every SKU personally. Killing one feels like killing a child. But the 15-SKU lineup includes 4 that haven't earned their shelf space in 18 months.
- **$10M–$15M:** The COO or VP Sales. They know the portfolio is bloated but nobody has done the analysis to prove which SKUs to cut. The conversation keeps getting deferred because "we don't have the data."
- **$15M–$20M:** The CEO and CFO together. The board is asking about margin improvement. SKU rationalization is the single highest-leverage margin play available — but it requires analysis nobody has time to do.

**How it compounds:** Every new SKU added to an already-bloated portfolio makes the problem worse. The brand adds "Smoky Habanero" to the lineup, which cannibalizes "Original" and "Chipotle Lime," dragging all three below the velocity threshold. Now three SKUs are at risk of delisting instead of one. The proliferation doesn't grow linearly — it grows combinatorially across retailers.

#### The Status Quo

The CEO asks: "Should we kill any SKUs?" The sales lead says "probably" but can't say which ones with confidence. The broker says "the buyer likes the full assortment" (the broker gets paid on revenue, not margin). The CFO can produce revenue by SKU but not contribution by SKU after all loaded costs. Nobody can answer: "What does it actually cost to keep this SKU on shelf at Walmart for a year?"

So nothing gets killed. The portfolio grows. Margin erodes. Production gets more complex. The team manages more SKUs with the same headcount.

---

### 2. Why This Piece

**Expands the most-asked-about module in the Velocity Decision Tool.** The Velocity Tool has 8 modules; SKU Rationalization is Module 6. It ranks SKUs by velocity and flags underperformers. Prospects who use the Velocity Tool consistently ask: "Can you go deeper on the SKU analysis?" This piece is the deeper version.

**Multi-dimensional vs. single-dimensional.** The Velocity Tool module uses velocity as the sole lens. The standalone Framework uses five dimensions: velocity × contribution margin × shelf-space cost × production complexity × cannibalization risk. That's the difference between "this SKU is slow" and "this SKU is slow, margin-negative, costs $8K/year to maintain at Walmart, adds 2 hours of changeover per production run, and cannibalizes your best seller."

**The highest-leverage margin play at $10M–$30M.** Killing 10–15 SKUs from a 60-SKU portfolio can save $100K–$300K/year in loaded costs and free shelf space, production capacity, and management attention for higher-performing items or new launches. No other single action at this stage delivers comparable margin improvement with this little risk.

**All-tier applicability:** $3M brand with 15 SKUs benefits (kill 3, save $30K). $20M brand with 90 SKUs benefits (kill 15, save $250K). Same framework, different scale.

**Compounds with multiple existing pieces:**
- **Velocity Decision Tool (#1):** The Framework is the deeper version of Module 6. They cross-reference naturally.
- **Where the Money Actually Comes From (#2a):** Channel profitability reveals which channels erode margin; SKU rationalization reveals which SKUs erode margin within those channels. Two lenses on the same margin problem.
- **Retail Readiness Scorecard (#195):** One readiness dimension is "can we ship?" A tighter SKU portfolio makes fulfillment simpler and OTIF scores higher.
- **The 150 Cases (#2):** Fewer SKUs = fewer fulfillment failure modes = fewer short-ships.
- **Cinderhaven Data Platform (#7a):** Consumes from the platform's product master, velocity, chargeback, and cost marts.

---

### 3. The Portfolio Piece

#### Structure

**Part 1 — The hook: the framework itself**

A multi-dimensional scoring matrix applied to every SKU in the portfolio. Five dimensions, each scored 1–5:

| Dimension | What It Measures | Data Source |
|-----------|-----------------|-------------|
| **Velocity** | Units/store/week relative to category and retailer threshold | Retailer POS data or broker velocity reports |
| **Contribution margin** | Per-unit margin after ALL loaded costs (COGS + slotting amortized + trade spend + chargebacks + freight) | ERP + deduction crosswalk |
| **Shelf-space cost** | Annual cost to maintain this SKU on shelf at each retailer (slotting amortization + trade spend + data maintenance + broker time) | Calculated from retailer cost data |
| **Production complexity** | Changeover time, minimum run size, ingredient sourcing difficulty, co-packer capacity consumed | Co-packer data + production schedule |
| **Cannibalization risk** | Does this SKU measurably reduce velocity of a higher-margin sibling? | Cross-elasticity analysis from POS data |

Optional 6th dimension: **Strategic value** — brand builder, line filler, entry-point product, seasonal. A qualitative override for SKUs that fail the quantitative matrix but have non-financial strategic value. The framework surfaces these explicitly so the CEO can make a conscious choice: "I'm keeping this SKU despite the math because it's the brand's flagship. That decision costs $35K/year. I accept that."

**The output — four quadrants:**

| Recommendation | Criteria | Action |
|---------------|----------|--------|
| **Double down** | High velocity, high margin, low cost, no cannibalization | Invest: more shelf space, more promos, production priority |
| **Maintain** | Adequate across dimensions, no red flags | Keep as-is, monitor quarterly |
| **Fix or kill** | Fails one dimension badly, fixable root cause identified | Specific fix with timeline; if not fixed in 90 days, delist |
| **Kill** | Fails two or more dimensions, no fix available | Delist. Quantify savings. Reallocate resources to "double down" SKUs. |

**Part 2 — The proof: Cinderhaven's 50-SKU portfolio analysis**

Cinderhaven has 50 SKUs across five product lines (Artisan Sauces, Pantry Staples, Specialty Condiments, Dried Goods, Snack Bites). The framework scores all 50 into four quadrants:

| Recommendation | SKU Count | % of Portfolio |
|---------------|:---------:|:--------------:|
| Double down | 1 | 2% |
| Maintain | 16 | 32% |
| Fix or kill | 14 | 28% |
| Kill | 19 | 38% |

The headline finding: **19 of Cinderhaven's 50 SKUs (38%) score in the "kill" quadrant — net-negative on loaded margin once shelf-space, production complexity, and cannibalization costs are attributed.** Delisting them frees shelf space, production capacity, and management attention for higher-performing items or new launches. (Per-SKU revenue and loaded-cost detail comes from the live scoring tool; figures here are the current pipeline output, not estimates.)

The "fix or kill" 15 are even more interesting. Each one has a specific issue:
- 4 SKUs with velocity below retailer threshold at one retailer but above at another (fix: delist at the underperforming retailer, maintain at the strong one)
- 3 SKUs with negative contribution margin driven entirely by chargeback rates (fix: resolve the product data error causing the chargebacks)
- 5 SKUs cannibalizing higher-margin siblings (fix: differentiate positioning or consolidate into the stronger SKU)
- 3 SKUs with production complexity disproportionate to their contribution (fix: consolidate production runs or reformulate)

**Part 3 — The evidence: the technical artifacts**

- **Streamlit interactive tool** — user uploads SKU data (velocity, COGS, retailer costs) or connects to sample Cinderhaven data. Tool produces the five-dimensional scoring matrix, quadrant assignment per SKU, and a "kill list" with quantified annual savings.
- **Excel financial model** — CFO-grade. Scenario analysis: "What happens to total margin if we kill these 19 SKUs? What if we kill 12 and fix 7?" Sensitivity on velocity assumptions and cost allocation methodology.
- **Cinderhaven case study** — HTML + PDF report walking through the full portfolio analysis, findings per product line, and the prioritized kill list and savings opportunity.
- **SQL diagnostic queries** — queries against the Cinderhaven Data Platform that produce the inputs for each dimension (velocity ranking, loaded contribution by SKU, shelf-space cost calculation, cannibalization detection).

#### The Margin Math

For a $25M brand with 60–90 SKUs:

- **Direct cost savings from killing bottom-tier SKUs:** $80K–$300K/year. Slotting fee savings + trade spend reduction + warehouse space freed + data maintenance reduction.
- **Production efficiency gain:** Fewer changeovers = 10–20% more usable co-packer capacity. At $25M with constrained co-packer capacity, that's worth $200K–$500K in potential additional production without adding capacity.
- **Velocity improvement on remaining SKUs:** Shelf space freed by killed SKUs goes to "double down" SKUs. More facings = better velocity = stronger position at category review. The velocity uplift is retailer-specific but conservatively 5–15% on the SKUs that gain space.
- **Reduced management complexity:** Fewer SKUs = fewer POs, fewer item setups, fewer deduction disputes, fewer data quality issues. Hard to quantify but real — it's the difference between the ops team being reactive and being strategic.
- **Cannibalization reversal:** When a cannibalizing SKU is killed, the parent SKU's velocity recovers. If the parent has higher margin, the net contribution improvement exceeds the revenue lost from the kill.

**Total estimated value of a rationalization exercise: $150K–$500K/year** at $25M revenue. Recurring, because the portfolio stays tighter going forward.

#### Before / After

- **Before:** CEO reviews the quarterly velocity report. Sees 19 SKUs below threshold. Asks: "Should we cut any?" Sales lead says "probably not — the buyer likes the assortment." CFO can't quantify the cost of keeping them. Nothing changes. Margin continues to erode. Next quarter, 22 SKUs are below threshold.

- **After:** CEO opens the rationalization framework. Sees the four-quadrant view. The bottom 19 are clearly net-negative — their loaded cost exceeds their contribution. The "fix or kill" 14 each have a specific diagnosis and timeline. CEO tells sales lead: "We're cutting these 19 and fixing these 14. Here's the math for the buyer conversation." The buyer says "fine, we can use that shelf space." The brand's average velocity-per-SKU improves. Next category review goes better.

#### Who Else Sees This?

- **Primary:** CEO, VP Sales, COO. The people who make the keep/kill decision.
- **Secondary:** CFO (validates the financial model), broker (needs the data to have the buyer conversation about delisting), buyer at the retailer (actually prefers a tighter assortment from the brand — fewer slow SKUs means better category productivity).
- **How it gets shared:** CEO uses the framework internally to make the decision. Sales lead takes the "kill list with math" to the broker. Broker uses the financial rationale in the buyer conversation: "The brand is rationalizing to their top performers — here's the velocity improvement you'll see."

---

### 4. Technical Specification

#### Repo

- **Repo name:** `sku-rationalization`
- **Repo description:** Multi-dimensional SKU rationalization framework for specialty food brands. Scores SKUs on velocity × margin × shelf-space cost × production complexity × cannibalization risk. Interactive Streamlit tool, Excel financial model, Cinderhaven case study.

#### Tech Stack

| Tool | Role |
|------|------|
| Python | Scoring engine, data processing, cannibalization detection |
| Streamlit | Interactive tool — upload SKU data, get scoring matrix + kill list |
| Cinderhaven Data Platform (Postgres) | Source of truth for Cinderhaven case study |
| dbt | Models for loaded contribution by SKU, shelf-space cost allocation, cannibalization detection |
| Excel / openpyxl | Financial model with scenario analysis |
| Plotly | Visualizations — scatter plots (velocity vs margin, colored by recommendation), waterfall (savings from rationalization) |
| pandas | Data manipulation, scoring logic |

#### Deliverables

| Deliverable | Format | Purpose |
|------------|--------|---------|
| Interactive rationalization tool | Streamlit, hosted | Prospect plays with it, sees their own portfolio scored |
| Excel financial model | .xlsx download | CFO scenarios — "what if we kill these 19?" |
| Cinderhaven case study | HTML + PDF | Proof — 50-SKU portfolio analyzed, kill list identified |
| SQL diagnostic queries | .sql files in repo | Platform query examples for each scoring dimension |
| Scoring methodology doc | Markdown in repo | Transparency on how each dimension is scored and weighted |

#### Deployment

- **Streamlit tool:** Streamlit Community Cloud.
- **Excel model:** Downloadable from tool or portfolio site. Email-gated or open.
- **How prospects find it:** LinkedIn post with the four-quadrant scatter plot. SEO on "SKU rationalization specialty food," "which SKUs to cut food brand," "SKU portfolio optimization." Cross-linked from Velocity Decision Tool.

#### Source Data

Consumes from Cinderhaven Data Platform marts:

| Mart | Purpose |
|------|---------|
| `dim_products` | SKU master, product lines, pack sizes |
| `fct_velocity` or velocity-derived views | Units/store/week by SKU by retailer |
| `fct_chargebacks` + `fct_deductions` | Per-SKU chargeback and deduction rates |
| `dim_costs` | COGS, slotting amortization, trade spend allocation by SKU |
| `fct_orders` | Sales volume for cannibalization analysis |

New dbt models specific to this piece:
- `int_loaded_contribution_by_sku` — per-SKU margin after all costs
- `int_shelf_space_cost_by_sku` — annual cost to maintain each SKU per retailer
- `int_cannibalization_pairs` — SKU pairs where one reduces the other's velocity

---

### 5. Skills Demonstrated

- **Multi-dimensional portfolio analysis** — five-dimension scoring matrix is more sophisticated than any single-metric ranking. Demonstrates structured analytical thinking.
- **Cost allocation methodology** — allocating slotting, trade spend, production complexity, and overhead to the SKU level. This is accounting-adjacent work that most data analysts can't do and most accountants don't.
- **Cannibalization detection** — cross-elasticity analysis from POS data. One of the few genuinely analytical (not just diagnostic) techniques in the portfolio.
- **Decision framework design** — the four-quadrant output (double down / maintain / fix or kill / kill) is a decision framework, not a report. The practice's core positioning is decision infrastructure.
- **Excel financial modeling** — scenario analysis in a CFO-grade model. Complements Where the Money's Excel model.

---

### 6. Foot-in-the-Door Offering

- **Offering name:** SKU Portfolio Audit
- **Format:** Fixed-fee 2–3 week engagement
- **Price range:** $15K–$25K
- **What the client gets:**
  1. Five-dimensional scoring of every SKU in the portfolio
  2. Four-quadrant classification (double down / maintain / fix or kill / kill)
  3. Kill list with quantified annual savings per SKU
  4. Fix list with specific diagnosis and timeline per SKU
  5. Cannibalization analysis — which SKUs are stealing from which
  6. Scenario modeling — margin impact of various rationalization levels
  7. Excel financial model tuned to the client's data
  8. Buyer conversation brief — the sales narrative for delisting underperformers
- **Why this piece sells it:** The Streamlit tool gives a directional score using uploaded data or defaults. The engagement delivers the full analysis with real loaded costs, real cannibalization data, and the sales narrative the brand needs to execute the delisting conversation with the buyer.

#### Client Lift

- **What the client has to do:** One 45-minute kickoff. Provide: SKU master with COGS, last 12 months of velocity data by SKU by retailer, slotting fee records, trade spend by SKU if available, co-packer production schedule (for changeover analysis). ~3–4 hours of ops/finance time total.
- **What we need:** ERP product master, velocity data (from retailer portals or broker reports), cost data (slotting, trade, production).

#### The DIY Defense

- **Loaded contribution by SKU is harder than it looks.** Revenue by SKU is easy. COGS by SKU is usually available. But allocating slotting amortization, trade spend, chargeback rates, freight, and production complexity overhead to the SKU level requires methodology decisions the CFO hasn't made. The framework makes those decisions systematically.
- **Cannibalization requires cross-elasticity analysis.** "Did our Chipotle Lime actually bring new buyers, or did it split the Original buyer in two?" Answering this requires comparing store-level velocity before and after the variant launched, controlling for seasonality and promos. An analyst can do this given 2 weeks; the framework does it systematically across all SKU pairs.
- **The buyer conversation needs financial data, not opinions.** "We want to delist 5 SKUs" without quantified rationale is a weak ask. "We're delisting 5 SKUs that average 1.8 units/store/week — below your category threshold — and reallocating that shelf space to our top 3 performers at 8.5 units/store/week. Here's the velocity improvement the category gets." That conversation requires the framework's output.

---

### 7. Marketing / Distribution

- **Portfolio integration:** Cross-linked from the Velocity Decision Tool ("Want to go deeper on SKU rationalization? Here's the full framework."). Referenced in Where the Money's channel analysis ("Your Walmart contribution includes SKUs that are individually net-negative").
- **LinkedIn:**
  - Launch post: "A $25M food brand's bottom 19 SKUs score net-negative on loaded margin — their cost to carry exceeds their contribution. Here's the framework that finds them." Pair with the four-quadrant scatter plot.
  - Follow-up: "The hardest conversation in specialty food isn't 'which retailer should we pursue?' It's 'which SKUs should we kill?'" The emotional angle.
- **SEO:** "SKU rationalization specialty food," "which SKUs to cut food brand," "SKU portfolio optimization CPG," "product line rationalization framework," "SKU profitability analysis"
- **Shareability:** The four-quadrant scatter plot (velocity vs margin, colored by recommendation) is the shareable visual. Brokers and sales leads share this with their CEO.
- **Lead capture:** Streamlit tool ungated. Excel model email-gated. Case study open.

---

### 8. Competitor / Existing Content Scan

- **What exists:**
  - **Consulting firm SKU rationalization white papers** (McKinsey, Bain, BCG) — strategic level, enterprise framing ($500M+ companies), not interactive.
  - **CPG analytics platform features** (Crisp, Alloy.ai) — SKU analytics as one feature among many. Not standalone, not a framework, not specialty-food-specific.
  - **Trade press articles** — occasional "how to rationalize your portfolio" pieces. Anecdotal, not quantitative, not interactive.
  - **Generic portfolio analysis tools** — BCG matrix (growth vs share) applied to CPG. Too high-level, doesn't account for loaded costs or cannibalization.
- **What's missing:**
  - Multi-dimensional framework specific to specialty food brands at $10M–$30M
  - Interactive tool where you can upload your own data
  - Loaded-cost methodology (not just revenue or gross margin, but ALL costs allocated to the SKU)
  - Cannibalization analysis as an explicit dimension
  - The "buyer conversation brief" — output designed to support the delisting conversation with the retailer
- **Your angle:**
  1. Five dimensions, not one (velocity alone is necessary but insufficient)
  2. Loaded cost allocation (slotting, trade, production, data maintenance all counted)
  3. Cannibalization detection built in
  4. Interactive tool + Excel model + case study
  5. Output designed for the buyer conversation, not just internal analysis
  6. Specialty food specific at $10M–$30M

---

### 9. Cinderhaven Integration

- **Consumes from the Cinderhaven Data Platform.** All five scoring dimensions pull from existing or new-build marts on the platform.
- **Adds three dbt models:**
  - `int_loaded_contribution_by_sku` — full per-SKU margin calculation
  - `int_shelf_space_cost_by_sku` — annual cost to maintain per retailer
  - `int_cannibalization_pairs` — cross-elasticity between SKU pairs
- **50 SKUs analyzed.** The case study covers the full Cinderhaven portfolio. Findings by product line (Artisan Sauces, Pantry Staples, Specialty Condiments, Dried Goods, Snack Bites) add realism — the kill list doesn't just cluster in one line.
- **Consistency:** SKU velocity data aligns with Velocity Decision Tool outputs. Loaded contribution aligns with Where the Money's channel analysis (if you sum SKU contributions by channel, they should match the channel-level numbers). Cross-portfolio consistency is the Cinderhaven Data Platform's job.

---

### 10. Tactical Notes

- **The sunk cost fallacy is the emotional center of this piece.** "We already paid the slotting fee" is the single most common reason brands keep dying SKUs alive. The framework must address this explicitly: "The slotting fee is gone. The question is what it costs you THIS YEAR to maintain a shelf position that isn't earning its keep."
- **The buyer conversation brief is the secret weapon.** Most brands can identify their slow SKUs. What they can't do is articulate the delisting request to the buyer in financial terms the buyer cares about. "Delisting these 5 SKUs improves category productivity by X% — here's the velocity math" is a conversation that respects the buyer's perspective. Producing this brief is what makes the framework more than an analysis tool.
- **Production complexity is the dimension most brands don't have data for.** Co-packer changeover time by SKU is often not tracked. The framework should handle this gracefully — either accept the data if available, or use a reasonable proxy (number of unique ingredients, pack format differences, allergen changeover requirements).
- **Cannibalization is the most technically demanding dimension.** True cross-elasticity requires controlled comparison (stores with the variant vs. stores without, controlling for time and geography). If the data supports it, do it properly. If not, use a simpler proxy: did the parent SKU's velocity decline in the quarter the variant launched? Acknowledge the limitation.
- **Don't make this a "kill everything" piece.** The four-quadrant framework must include "double down" and "maintain" prominently. Brands fear that rationalization means "cut everything to the bone." Show that it means "invest more in your winners while cleaning up the drag."

#### The Credibility Marker

Knowing that retailer buyers at Walmart and Costco actually PREFER a tighter assortment from specialty brands — the buyer's job is category productivity, not brand assortment breadth. A brand that voluntarily rationalizes and presents the velocity improvement math is a more sophisticated vendor than one that clings to every SKU. This insight — that the buyer is your ally in rationalization, not your adversary — is the kind of practitioner knowledge that marks the framework as built by someone who's been in the buyer meeting.

Secondary markers:
- Understanding that slotting fees should be amortized over expected SKU life (2–3 years typical for specialty food at mass retail), not expensed in year one
- Knowing that production changeover costs for specialty food vary dramatically by product type (a sauce line changeover is 2–4 hours; an allergen changeover is 8+ hours)
- Awareness that "strategic value" overrides the math in specific cases (the brand's hero SKU might be velocity-negative at one retailer but is the brand's identity — that's a conscious decision, not an oversight)

#### Data Paranoia / Security

- **What's sensitive:** SKU-level margin data, production costs, slotting fees by retailer. Brands are extremely protective of this — it's the operational DNA of the business.
- **How the narrative reassures:** Cinderhaven's numbers are synthetic. The engagement uses standard NDA. The Excel model runs locally. The Streamlit tool doesn't store uploaded data. Engagement deliverables can anonymize retailer names.

---

### 11. Open Questions

- [ ] **Streamlit tool scope.** Full upload-your-data interactive scoring vs. pre-built Cinderhaven demonstration with limited interactivity? Full interactive is more lead-gen but bigger build. Recommendation: full interactive — this is the piece where playing with your own data drives conversion.
- [ ] **Cannibalization methodology.** Full cross-elasticity (rigorous but data-intensive) vs. simpler launch-impact proxy (practical but less defensible)? Recommendation: offer both — full method if the data supports it, proxy if not, with methodology notes.
- [ ] **Number of scoring dimensions.** Five is the current design. Could expand to six (add strategic value as a quantified dimension) or contract to four (merge shelf-space cost into contribution margin). Recommendation: keep five + strategic value as a qualitative override, not a sixth scored dimension.
- [ ] **Platform integration.** Add the three new dbt models to the Cinderhaven Data Platform repo, or keep them in the SKU rationalization repo? Recommendation: add to the platform — they serve other consumers (Where the Money could reference loaded SKU contribution).
- [ ] **Gating.** Streamlit tool ungated. Excel model email-gated? Recommendation: yes — the Excel model is the high-value CFO asset.

---

### 12. Build Estimate

- **Effort level:** Medium. Extends existing Velocity Tool logic with additional dimensions. Co-packer data generation and cannibalization methodology are the harder parts.
- **Time estimate:** ~2–3 weeks elapsed with Claude Code.

| Work item | Bottleneck | Time |
|-----------|-----------|------|
| Cost allocation methodology (how to calculate loaded contribution + shelf cost per SKU) | Design (you) | 2–3 days |
| dbt models (loaded contribution, shelf-space cost, cannibalization pairs) | Code | 2–3 days |
| Cannibalization detection logic | Code + design | 2–3 days |
| Scoring engine (5-dimension matrix, quadrant assignment) | Code | 1–2 days |
| Streamlit interactive tool (upload, score, visualize, download) | Code | 3–4 days |
| Excel financial model (scenarios, kill-list savings, sensitivity) | Code + design | 2–3 days |
| Cinderhaven 50-SKU case study (run framework, write findings) | Code + writing | 2–3 days |
| Scatter plot + waterfall visuals | Code | 1 day |
| Methodology documentation | Writing | 1 day |
| Polish | Both | 2 days |

- **Dependencies:** Cinderhaven Data Platform (for case study data — already built). Velocity data and cost data must exist in the platform. Co-packer production data may need to be generated as a new synthetic layer.
- **New skills required:** Cross-elasticity / cannibalization detection (new analytical technique). Multi-dimensional scoring framework design (new pattern).

#### Out of Scope

- **New product launch recommendations.** The framework rationalizes what exists; it doesn't recommend what to launch next. (Adjacent piece: #41 New SKU velocity vs forecast in the brainstorm list.)
- **Retailer-by-retailer assortment optimization.** The framework scores SKUs across the portfolio. Retailer-specific assortment optimization (which SKUs at which retailers) is a deeper version that belongs in engagement work.
- **Pricing optimization.** The framework identifies SKUs that are margin-negative; it doesn't recommend what to price them at. (Adjacent: price elasticity analysis from the brainstorm list.)
- **Implementation / delisting execution.** The framework recommends what to cut; the practice doesn't manage the delisting conversations or retailer negotiations.

---

### Relationship to Existing Inventory

| Project | Relationship |
|---------|-------------|
| Velocity Decision Tool (#1, built) | **Parent piece.** The Framework is Module 6 expanded. Cross-linked: "Want to go deeper? Here's the full framework." |
| Where the Money Actually Comes From (#2a, in build) | **Complementary lens.** Where the Money shows channel-level contribution; this shows SKU-level contribution. Together they answer "which channels AND which SKUs are making money." |
| Product Data Health Audit (#6, built) | **Upstream cause.** Some "fix or kill" SKUs have chargeback issues driven by product data errors. The fix may be a data quality fix, not a delist. |
| Retail Readiness Scorecard (#195, briefed) | **Readiness input.** A tighter portfolio is more ready for a new retailer launch. |
| The 150 Cases (#2, built) | **Downstream effect.** Fewer SKUs = fewer fulfillment failure modes. |
| Brainstorm #42 Cannibalization detection (21) | **Absorbed.** The cannibalization dimension of this framework IS that brainstorm idea. |
| Brainstorm #97 SKU clustering velocity-margin-volatility (23) | **Absorbed.** The five-dimension scoring IS the clustering. |
| Umbrella Positioning Piece (#3) | **Decision 1.** "Which SKUs should we keep, kill, or double down on?" |

---

*Brief complete when open questions are resolved.*
