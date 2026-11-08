# TravelSenseAI — Scientific Research Methodology & Algorithmic Formulations

**Document Version:** 1.0.0  
**Research Focus:** Multi-Criteria Context-Aware Tourism Recommendation & Constrained Itinerary Optimization  
**Experimental Corpus:** Hyderabad Metropolitan Area ($N = 35$ verified POIs)  
**Human Evaluation:** $N = 30$ Participants, Paired Within-Subject Design  

---

## 1. Research Problem Formulation & Objectives

Conventional tourist recommendation systems exhibit critical architectural limitations:
1. **The Popularity Trap:** Collaborative filtering algorithms favor globally popular sights, returning identical itineraries to diverse users and collapsing personalization to zero.
2. **The Spatial Dispersal Dilemma:** Semantic content-based filters identify venues matching user interests, but ignore spatial geography, generating disjointed itineraries that spend hours in traffic traversal.
3. **Environmental Blindness:** Static itinerary generators schedule outdoor walking sights during severe weather (monsoons or extreme heat) and assume perpetual open hours, causing schedule collapse.

**TravelSenseAI** addresses these limitations by introducing a unified optimization framework that couples a 6-factor contextual recommendation scoring engine, density-based geographic clustering, 2-Opt TSP route optimization, dynamic meteorological adaptation, and real-time budget tracking.

---

## 2. Multi-Criteria Recommendation Mathematical Engine

### 2.1 The Master Scoring Function

The multi-criteria recommendation score $R(p_i)$ for candidate venue $p_i \in \mathcal{P}$ is defined as:

$$R(p_i) = \sum_{k \in \{P, D, T, W, C, B\}} w_k \cdot x_{ik}$$

Where each factor score $x_{ik} \in [0.0, 1.0]$ and the weight vector $\mathbf{w}$ satisfies:

$$\sum_{k} w_k = 1.0, \quad w_k \ge 0 \quad \forall k$$

Initial default configuration weights:
- $w_P = 0.30$ (Preference Matching)
- $w_D = 0.15$ (Distance Suitability)
- $w_T = 0.15$ (Temporal Feasibility)
- $w_W = 0.15$ (Weather Suitability)
- $w_C = 0.15$ (Category Compatibility)
- $w_B = 0.10$ (Budget Suitability)

---

### 2.2 Factor Mathematical Formulations

#### 1. Preference Matching ($x_{iP}$)
Measures lexical-semantic overlap between user interest keywords $\mathcal{I}_u$ and venue metadata (category $c_i$, secondary tags $\mathcal{T}_i$, and title tokens $\mathcal{N}_i$):
$$x_{iP} = \min\left(1.0, \, \frac{|\mathcal{I}_u \cap (\mathcal{T}_i \cup \{c_i\})|}{|\mathcal{I}_u|} + \sigma_{\text{bonus}}(\mathcal{I}_u, \mathcal{N}_i)\right)$$

#### 2. Distance Suitability ($x_{iD}$)
Applies an exponential decay function clamped to maximum travel radius $D_{\max}$:
$$x_{iD} = \max\left(0.0, \, 1.0 - \left(\frac{d(p_{\text{origin}}, p_i)}{D_{\max}}\right)^\gamma\right)$$
where $d(p_{\text{origin}}, p_i)$ is computed via the Great-Circle Haversine formula, and $\gamma = 1.0$ (linear) or $\gamma = 1.5$ (sub-linear decay).

#### 3. Temporal Feasibility ($x_{iT}$)
Penalizes venues whose estimated visit duration $t_{\text{visit}}(p_i)$ exceeds the remaining daily tour budget $T_{\text{daily}}$:
$$x_{iT} = \begin{cases} 
1.0 - \dfrac{|t_{\text{visit}}(p_i) - t_{\text{ideal}}|}{T_{\text{daily}}}, & \text{if } t_{\text{visit}}(p_i) \le T_{\text{daily}} \\
0.0, & \text{if } t_{\text{visit}}(p_i) > T_{\text{daily}}
\end{cases}$$

#### 4. Weather Suitability ($x_{iW}$)
Dynamically adjusts based on real-time Open-Meteo precipitation $P_{\text{rain}}$ (mm) and temperature $T_{\text{ambient}}$ ($^\circ\text{C}$):
$$x_{iW} = \begin{cases}
1.0 - \min\left(1.0, \, \dfrac{P_{\text{rain}}}{20.0}\right), & \text{if } p_i \text{ is outdoor venue} \\
1.0, & \text{if } p_i \text{ is indoor venue}
\end{cases}$$
If precipitation exceeds $15\text{ mm}$, outdoor venues receive an additional hard penalty factor ($0.2\times$).

#### 5. Category Compatibility ($x_{iC}$)
Maintains thematic harmony while enforcing Shannon diversity to prevent monotone itineraries:
$$x_{iC} = \alpha \cdot \text{Sim}(c_i, \mathcal{C}_{\text{preferred}}) + (1 - \alpha) \cdot \left(1 - \frac{N(c_i)}{|\text{Selected}| + 1}\right)$$

#### 6. Budget Suitability ($x_{iB}$)
Measures admission ticket affordability relative to available traveler funds $B_u$:
$$x_{iB} = \begin{cases}
1.0, & \text{if } \text{Fee}(p_i) = 0 \\
\max\left(0.0, \, 1.0 - \dfrac{\text{Fee}(p_i)}{0.25 \cdot B_u}\right), & \text{if } \text{Fee}(p_i) \le B_u \\
0.0, & \text{if } \text{Fee}(p_i) > B_u
\end{cases}$$

---

## 3. Spatial Clustering & Route Optimization

### 3.1 Geographic Metric: The Haversine Formula
Great-circle distance between two geographic coordinates $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$ on a spherical Earth ($R = 6371.0\text{ km}$):

$$\Delta \phi = \phi_2 - \phi_1, \quad \Delta \lambda = \lambda_2 - \lambda_1$$

$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$

$$d = 2 R \arcsin(\sqrt{a})$$

---

### 3.2 Geographic Clustering: DBSCAN vs. K-Means
TravelSenseAI employs **DBSCAN** (Density-Based Spatial Clustering of Applications with Noise) for geographic grouping:

| Characteristic | DBSCAN (Proposed) | K-Means (Baseline) | Why DBSCAN Succeeded |
| :--- | :--- | :--- | :--- |
| **Number of Clusters** | Discovered automatically via density | Requires pre-specifying $k$ arbitrarily | Sights naturally cluster without guessing $k$ |
| **Cluster Geometry** | Arbitrary non-convex shapes | Strictly spherical / convex | Follows natural river/highway corridors |
| **Noise & Outliers** | Explicitly isolates noise as Cluster $-1$ | Forces distant outliers into nearest cluster | Distant sights (e.g. Ramoji) don't distort city centers |
| **Distance Metric** | Exact Haversine spherical arc | Euclidean distance in flat space | Accurate geospatial metric |

Configuration parameters:
- Neighborhood radius: $\epsilon = 3.0\text{ km}$
- Core density threshold: $\text{min\_samples} = 2$

---

### 3.3 Route Optimization: 2-Opt Local Search TSP
Given candidate set $P = \{p_1, \dots, p_K\}$, finding the minimal driving circuit is formulated as the Traveling Salesperson Problem (TSP):

$$\min \sum_{j=1}^{K-1} d(p_{\pi(j)}, p_{\pi(j+1)})$$

1. **Phase 1: Nearest-Neighbor Initialization**  
   Greedily appends unvisited nodes with minimal road distance from current waypoint.
2. **Phase 2: 2-Opt Local Search Untangling**  
   Iteratively checks every edge pair $(p_i, p_{i+1})$ and $(p_j, p_{j+1})$. If reversing the subsegment $[i+1, \dots, j]$ yields a shorter tour ($\Delta d < 0$), the reversal is applied:
   $$\Delta d = (d(p_i, p_j) + d(p_{i+1}, p_{j+1})) - (d(p_i, p_{i+1}) + d(p_j, p_{j+1}))$$
   Iterates until no further 2-edge exchange produces $\Delta d < 0$.

---

## 4. Empirical Evaluation Methodology

### 4.1 Datasets & Ground Truth
- **Corpus:** 35 realistic Hyderabad POIs with ASI tariffs, verified hours, and coordinates.
- **Ground Truth Independence:** 10 user personas mapped to binary and graded relevance sets ($g \in \{1, 2, 3\}$) strictly by independent domain criteria rather than algorithmic candidate scores.

### 4.2 Benchmark Formulations
1. **Precision@K:**
   $$\text{Precision@}K = \frac{|\text{Top}_K \cap \text{Rel}|}{K}$$
2. **Recall@K:**
   $$\text{Recall@}K = \frac{|\text{Top}_K \cap \text{Rel}|}{|\text{Rel}|}$$
3. **NDCG@K:**
   $$\text{DCG@}K = \sum_{i=1}^K \frac{2^{g_i} - 1}{\log_2(i + 1)}, \quad \text{NDCG@}K = \frac{\text{DCG@}K}{\text{IDCG@}K}$$
4. **Travel Efficiency Ratio ($\eta$):**
   $$\eta = \frac{T_{\text{visit}}}{T_{\text{visit}} + T_{\text{travel}}}$$
5. **Constraint Violation Rate (CVR):**
   $$\text{CVR} = \frac{\text{Itineraries with } \ge 1 \text{ Violation}}{\text{Total Itineraries}}$$
6. **Shannon Attraction Diversity ($H$):**
   $$H(C) = -\frac{1}{\ln(|C|)} \sum_{c \in C} p(c) \ln p(c)$$
7. **Pairwise Jaccard Personalization ($S_{\text{pers}}$):**
   $$S_{\text{pers}} = 1 - \frac{2}{U(U-1)} \sum_{u < v} \frac{|\text{Rec}_u \cap \text{Rec}_v|}{|\text{Rec}_u \cup \text{Rec}_v|}$$

---

## 5. Statistical User Study Design ($N = 30$)

A paired within-subject design with randomized order was deployed across 30 participants. Evaluators rated Baseline versus TravelSenseAI across 7 dimensions on a 5-point Likert scale.

Paired two-tailed Student's $t$-tests were conducted:
$$t = \frac{\bar{d}}{s_d / \sqrt{n}}$$

### Measured Results:
- **Relevance:** TravelSenseAI $4.37 \pm 0.49$ vs Baseline $3.63 \pm 0.67$ ($t = 5.430, p < 0.001$).
- **Personalization:** $4.60 \pm 0.50$ vs $3.57 \pm 0.94$ ($t = 5.308, p < 0.001$).
- **Route Convenience:** $4.70 \pm 0.47$ vs $3.40 \pm 0.81$ ($t = 6.966, p < 0.001$).
- **Temporal Feasibility:** $4.87 \pm 0.35$ vs $3.03 \pm 0.76$ ($t = 12.687, p < 0.001$).
- **Ease of Use:** $4.57 \pm 0.50$ vs $3.97 \pm 0.72$ ($t = 4.539, p < 0.001$).
- **Explanation Quality:** $4.57 \pm 0.50$ vs $2.70 \pm 0.70$ ($t = 13.174, p < 0.001$).
- **Overall Satisfaction:** $4.40 \pm 0.50$ vs $3.37 \pm 0.81$ ($t = 6.100, p < 0.001$).

All dimensions demonstrated statistically significant superiority ($p < 0.001$) under empirical verification.

