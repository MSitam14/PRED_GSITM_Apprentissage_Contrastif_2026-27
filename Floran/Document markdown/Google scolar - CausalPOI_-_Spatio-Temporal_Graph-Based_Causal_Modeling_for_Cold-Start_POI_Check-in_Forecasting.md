---
source: Document/Google scolar/CausalPOI_-_Spatio-Temporal_Graph-Based_Causal_Modeling_for_Cold-Start_POI_Check-in_Forecasting.pdf
pages: 11
---

# CausalPOI: Spatio-Temporal Graph-Based Causal Modeling for Cold-Start POI Check-in Forecasting

Zhaoqi Zhang Nanyang Technological University Singapore, Singapore zhaoqi001@e.ntu.edu.sg Linyou Cai Meituan Beijing, China cailinyou@meituan.com

## Abstract

As urban environments continue to evolve rapidly, accurately modeling the dynamic behaviour of Points of Interest is essential for supporting data-driven urban planning and commercial decisionmaking. While recent advancements in spatio-temporal graph learning have improved POI forecasting, most methods rely on proximitybased graphs and correlation-driven modeling, which overlook the functional dependencies between POIs and fail to capture the causal effects of urban interventions. In this paper, we introduce a novel research problem – cold-start POI check-in forecasting, which aims to predict the future check-in pattern of a newly introduced POI, by modeling its temporal evolution and functional interactions with nearby POIs in a structured urban spatial context. To address these challenges, we propose CausalPOI, a spatio-temporal graph-based causal representation learning framework. CausalPOI leverages Spatio-Temporal Functional Interaction Graph to model semantic and spatial relationships between POIs, and constructs structurally aligned treatment and control graphs to simulate factual and counterfactual scenarios. Extensive experiments on real-world SafeGraph datasets demonstrate that CausalPOI significantly outperforms state-of-the-art baselines across the board, validating its effectiveness in spatio-temporal forecasting, semantic interaction modeling, and causal effect estimation, providing a more interpretable and actionable foundation for urban intervention analysis. Source code is available at Github 1.

CCS Concepts

- Information systems → Geographic information systems; • Computing methodologies → Temporal reasoning; Causal reasoning and diagnostics.

Keywords Cold-Start POI check-in forecasting, spatio-temporal graph neural networks, causal inference, urban computing 1https://github.com/ZZQ-NTU/CausalPOI This work is licensed under a Creative Commons Attribution 4.0 International License. KDD ’26, Jeju Island, Republic of Korea © 2026 Copyright held by the owner/author(s). ACM ISBN 979-8-4007-2259-2/2026/08 https://doi.org/10.1145/3770855.3817641 Miao Xie China Agricultural University Yi Li Nanyang Technological University Beijing, China xiemiao@cau.edu.cn Singapore, Singapore liyi0067@e.ntu.edu.sg Siqiang Luo Nanyang Technological University Gao Cong Nanyang Technological University Singapore, Singapore siqiang.luo@ntu.edu.sg Singapore, Singapore gaocong@ntu.edu.sg ACM Reference Format: Zhaoqi Zhang, Miao Xie, Yi Li, Linyou Cai, Siqiang Luo, and Gao Cong. 2026. CausalPOI: Spatio-Temporal Graph-Based Causal Modeling for Cold-Start POI Check-in Forecasting. In Proceedings of the 32nd ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2 (KDD ’26), August 09–13, 2026, Jeju Island, Republic of Korea. ACM, New York, NY, USA, 11 pages. https://doi.org/10.1145/3770855.3817641

## 1 Introduction

Urban environments are inherently dynamic, characterized by the continuous emergence, evolution, and disappearance of Points of Interest (POIs) [32] such as restaurants, gyms, libraries, and retail stores. These POIs play a central role in shaping human mobility patterns, influencing economic vitality, and defining the spatial structure of cities. Understanding and forecasting POI-level behaviour is crucial for a wide range of applications, including commercial site selection, transportation planning, and public infrastructure deployment. Traditional forecasting methods have predominantly relied on large-scale spatio-temporal data—such as aggregated mobility flows or region-level check-in statistics—to model urban activity patterns. These approaches [13, 28] often utilize coarse-grained spatial features, treating urban space as a collection of homogeneous regions and relying on statistical correlations between them to predict future trends. While such models offer useful insights at the macro level, they struggle to capture the fine-grained dynamics and localized influence of individual POIs—such as temporal bursts in popularity, functional shifts over time, or competitive and complementary effects within dense urban clusters.

Consider a real-world scenario where a new gym is about to open in a busy urban neighbourhood. Before its launch, business operators and digital service platforms seek to answer a key question: How many people are expected to check in at this new facility in the coming weeks? Accurate forecasting of a newly introduced gym’s check-in volume is crucial for assessing membership demand, allocating fitness instructors and equipment, and planning class schedules. Unlike conventional forecasting tasks [7, 11, 26] that rely on a POI’s historical data, this setting involves predicting user activity for a cold-start POI—one with no prior behavioural observations. To make reliable predictions, the model must infer potential demand as a result of introducing the new gym into an existing urban ecosystem. This requires modeling not only spatial context KDD ’26, August 09–13, 2026, Jeju Island, Republic of Korea Zhaoqi Zhang et al.

and functional relationships with nearby POIs, but also understanding how the new POI might causally affect and be affected by its surrounding environment. For example, the presence of competitive gyms may negatively impact the newly added establishment’s popularity, while complementary businesses like smoothie bars may boost foot traffic. Such counterfactual reasoning is essential to distinguish true effects from spurious correlations, and cannot be fully captured by conventional predictive models, since they primarily focus on correlation rather than causality.

Recent studies [6, 24, 27, 33] have increasingly focused on modeling urban activity patterns using spatio-temporal data and graphbased approaches. In particular, Graph Neural Networks (GNNs) [2] have been widely adopted to capture spatial correlations and relational dependencies among POIs, often by constructing graphs based on geographic proximity. These methods have shown success in forecasting POI activity under settings where historical data is available and the urban topology remains relatively static. Additionally, early efforts in causal representation learning have explored the estimation of individual treatment effects (ITE) under the potential outcomes framework [14, 21], offering tools to reason about interventions from observational data.

Despite these advances, two fundamental challenges remain in modeling POI dynamics for decision-making: (1) Functional Interaction Modeling. Existing graph-based forecasting methods mainly rely on spatial proximity to define relationships, overlooking the semantic functionality and real-world interactions among POIs. This simplification limits the ability to model competition and complementarity, which are essential for accurate predictions and planning. (2) Causal Estimation in Structured Spaces. Although some methods attempt to estimate treatment effects, they often overlook the spatial structure of urban environments and rely on unstructured representations. Consequently, they fail to simulate how interventions, such as introducing a new POI, affect surrounding areas through spatial dependencies.

This paper introduces a novel research problem – how to model the causal effect of a newly introduced POI on urban mobility patterns by explicitly representing its temporal evolution and functional interaction with surrounding POIs, which can be formulated as a cold-start POI check-in forecasting problem. Different from prior region-level flow prediction or standard graph forecasting tasks, our setting focuses on POI-level intervention-aware forecasting under localized spatial interference, where the introduction of a new POI changes the local functional interaction context. To address the aforementioned challenges, we propose CausalPOI, a spatio-temporal graph-based representation learning framework for POI-level forecasting. CausalPOI integrates two key components: the Spatio-Temporal Functional Interaction Graph (ST-FIG) Module, which captures both spatial proximity and semantic functional relations among POIs, and the Causal Inference Module, which estimates the individual treatment effect (ITE) of newly introduced POIs by simulating counterfactual scenarios. In ST-FIG, interaction strengths are learned via contrastive pretraining, allowing the model to uncover latent semantic dependencies beyond physical distance. The causal module constructs structurally aligned treatment and control graphs and estimates ITE through a shared Graph Neural Network (GNN) encoder and temporal decoder. The key contributions of this paper are summarized as follows:

- We define a novel research problem: cold-start POI check-in forecasting, which aims to predict the future check-in pattern of a newly introduced POI, by modeling its temporal evolution and functional interactions with nearby POIs in a structured urban spatial context. This cold-start forecasting setting is critical for real-world decision-making, yet remains underexplored in existing literature. • We propose CausalPOI, a spatio-temporal causal representation learning framework tailored to this task. To the best of our knowledge, this is the first framework that systematically incorporates causal estimation at the POI level by simulating both factual and counterfactual outcomes, enabling fine-grained causal reasoning in urban analysis. CausalPOI comprises two key components: (1) Spatio-Temporal Functional Interaction Graph Module, which captures both spatial proximity and semantic functional relationships among POIs, allowing the model to uncover both competitive and complementary relationships that extend beyond mere geographic distance. (2) Causal Inference Module, which estimates the individual treatment effect of newly introduced POIs based on aligned treatment and control graph structures. • We conduct extensive experiments on cold-start POI check-in forecasting using real-world POI and check-in data from the US. The results demonstrate the effectiveness of CausalPOI in predicting post-introduction POI activity and estimating treatment effects. Compared to baselines, our method achieves notable improvements across all metrics. In particular, CausalPOI achieves up to 57.8% RMSE and 34.3% MAE reduction compared to the best-performing baseline on the most challenging region, demonstrating its robustness under cold-start conditions and its effectiveness in capturing causal effects in dynamic urban environments.

## 2 Related Work

### 2.1 POI Check-in Prediction

POI check-in prediction is commonly framed as a downstream task of urban representation learning, where the central goal is to derive informative region-level embeddings. In this line of research, spatial graphs are typically constructed using POIs, trajectories, or road networks, and the resulting embeddings are employed for tasks such as demand forecasting or mobility analysis. For example, Fu et al. [5] and Zhang et al. [30] model spatial autocorrelations and intra-region structures to support region-level check-in forecasting. More recent approaches, including Wu et al. [23] and Zhang et al. [31], further enhance regional representations by incorporating heterogeneous spatial signals through graph-based fusion or contrastive learning techniques. Li et al. [9] also investigate POI interactions by analyzing competitive relationships, highlighting the importance of functional dependencies in POI behaviour modeling.

However, these methods primarily focus on regional abstractions, which may overlook the nuanced dynamics of individual POIs. By formulating check-in prediction as a statistical aggregation at the regional level, they often fail to capture the evolving patterns of specific POIs—such as temporal bursts, localized trends, or functional shifts. A few studies attempt to directly model POIs. For instance, Tschernutter et al. [20] predict POI-level check-in volumes by modeling latent interactions among POIs. Nonetheless, these models generally assume static POI behaviour and lack the ability to capture temporal evolution or structural changes in local contexts.

### 2.2 Causal Modeling

Conventional POI forecasting models predominantly rely on statistical correlations observed in spatio-temporal data, limiting their capacity to uncover causal effects—especially in counterfactual scenarios, such as evaluating the impact of adding or removing a POI. To overcome these limitations, causal representation learning has recently garnered attention. Pioneering works such as TARNet and CFRNet [18], and DragonNet [19], leverage the potential outcomes framework to estimate ITE by learning representations that reduce confounding bias. However, these methods are primarily designed for tabular or sequential data and are not well-suited for structured spatial domains.

Meanwhile, graph-based causal inference has emerged as a promising direction for relational data. For example, CausalGNN [21] proposes to learn causal representations on static graphs by integrating intervention modeling with message passing, while HyperSCI [15] extends this line of work to higher-order relational structures. Yet, such methods often assume fixed graph topologies and lack mechanisms to handle dynamic spatial structures, which are common in urban environments. Additionally, they typically neglect the temporal evolution of spatial dependencies and the functional semantics of urban entities like POIs.

## 3 Preliminary

Definition 1 Point of Interest: A POI 𝑝 refers to a point with a geographic position, 𝑝.𝑔 = (𝑙𝑎𝑡𝑝,𝑙𝑜𝑛𝑝). It can be associated with a set of textual tags 𝑝.𝑡 = (𝑡1,𝑡2, ...,𝑡𝑖). Definition 2 POI Check-in sequence: Each POI 𝑝 has a check-in sequence 𝑝.𝑐 = {𝑐1,𝑐2, ...,𝑐𝑊 }, and each check-in record is denoted as a tuple 𝑐 = (𝑤,𝑛) indicating that the POI 𝑝 was visited 𝑛 times in the week w. Examples of POI and check-in sequence are provided in Table 4 in Appendix A. Problem Statement: We formally define the Cold-Start POI Checkin Forecasting problem as follows: Given a newly introduced POI 𝑝 with no historical check-in records, the objective is to (1) forecast its future check-in sequence 𝑝.𝑐ˆ = {𝑐ˆ1, ˆ𝑐2, . . . , ˆ𝑐W} over the next W weeks; and (2) estimate the individual treatment effect (ITE) of introducing 𝑝 by comparing the predicted outcomes under the factual scenario (with 𝑝 introduced) and the counterfactual scenario (without 𝑝). During training and evaluation, the ground-truth future check-in sequence 𝑝.𝑐 = {𝑐1,𝑐2, ...,𝑐𝑊 } is available as supervision.

## 4 Methodology

We model the cold-start POI check-in forecasting problem as a time series problem, which can better capture the trends and dynamic behaviours of POIs over time. Time series modeling accounts for temporal dependencies, identifying patterns in the evolution of POIs, and making more accurate predictions. To this end, we propose CausalPOI, a spatial-temporal graph-based causality-aware representation learning framework tailored to estimate the Individual Treatment Effect of newly introduced POIs. Unlike traditional approaches that rely on region-level aggregation, CausalPOI focuses on POI-level time series, enabling the model to recognize fine-grained behavioural patterns specific to different time periods. It explicitly models the counterfactual scenario in which the POI had not been introduced, allowing the framework to disentangle causal influence from mere correlation. Although our implementation builds upon standard graph representation learning components, the key novelty lies in the intervention-aware problem formulation and the causal graph construction for POI-level forecasting. Specifically, we construct paired treatment-control graphs for each newly introduced POI, enabling localized counterfactual reasoning beyond standard static graph prediction. ST-FIG further captures functional relations among neighbouring POIs rather than relying solely on geographic proximity. As illustrated in Figure 1, this end-to-end design encourages the learning of spatio-temporal representations that are both temporally consistent and causally informative, thus enabling reliable estimation of the evolving impact of new POIs.

### 4.1 Spatial-Temporal Functional Interaction Graph Module

The neighbour-based check-in volume captures activity driven by the presence and interaction of nearby POIs, particularly through competitive or complementary relationships. For instance, a gym may boost visits to a nearby smoothie bar due to their functional complementarity, while potentially experiencing decreased checkins from the emergence of a competing gym nearby. This component reflects the spatial and functional interplay among neighbouring POIs and its influence on individual check-in dynamics. To model these intricate interactions, we construct the Spatial- Temporal Functional Interaction Graph, which captures the evolving spatial, temporal, and functional dependencies among POIs. In this graph, each POI is represented as a node, and edges are established based on spatial proximity, temporal co-occurrence, and functional relationships such as competition and complementarity. This comprehensive structure enables the model to learn how nearby POIs influence each other over time, supporting more accurate and context-aware check-in prediction.

Given a newly added POI 𝑝, we collect a neighbourhood set 𝑁 = {𝑛1, ...,𝑛𝑖} comprising nearby POIs that may exhibit competitive or complementary effects due to geographic proximity, as determined by the following condition:

𝑑𝑖𝑠𝑡(𝑝,𝑛) = 𝐻𝑎𝑣𝑒𝑟𝑠𝑖𝑛𝑒(𝑙𝑎𝑡𝑝,𝑙𝑎𝑡𝑛,𝑙𝑜𝑛𝑝,𝑙𝑜𝑛𝑛,𝑟) ≤ 𝑚𝑎𝑥𝑑𝑖𝑠𝑡 (1)

where the 𝐻𝑎𝑣𝑒𝑟𝑠𝑖𝑛𝑒 formula calculates the great-circle distance between two points given their latitudes and longitudes, 𝑟 is the radius of the Earth, and 𝑚𝑎𝑥𝑑𝑖𝑠𝑡 is set to 1000m.

We then construct a POI functional interaction graph G, which is constructed as a 1-hop subgraph with the following principles:

- Node Definition: Each subgraph G comprises a POI-type target POI and its spatial neighbours, represented as neighbour-type nodes. Each node is initialized with textual embeddings derived from POI textual tags; • Edge Definition: For each neighbour POI 𝑛 ∈ 𝑁, we construct a directed edge from the neighbour POI 𝑛 to the target POI 𝑝, enabling bidirectional message passing. Each edge is assigned a weight 𝑤(𝑝,𝑛);

KDD ’26, August 09–13, 2026, Jeju Island, Republic of Korea Zhaoqi Zhang et al.

Input: Weekly Dynamic POI data Causal Inference Module where treatment and control graphs are encoded using shared Graph and Position Encoders, and their temporal evolution is modeled using a GRU to estimate the causal effect of the newly introduced POI.

- Temporal Modeling: For each newly added POI, we construct four temporal subgraphs corresponding to the first w weeks following its introduction. This design enables the model to capture early-stage interaction patterns and temporal dynamics of spatial influence. The temporal dynamics in ST-FIG are induced by the week-specific neighbourhood composition and activity context. Specifically, only POIs that are active in week w are included in Gw, causing the node set and aggregated neighborhood representations to evolve over time.

The textual embedding 𝐸𝑝 of the POI 𝑝 is obtained by encoding its textual tags using pre-trained BERT [4]:

𝐸𝑝 = BERT ( [CLS] 𝑡1,𝑡2, ...,𝑡𝑖 [SEP] ) (2)

where [CLS] represents the entire input sequence, while [SEP] is used to separate different segments.

To define the edge weight w(𝑝,𝑛) between a newly added POI 𝑝 and its neighbour 𝑛, we jointly consider their geographic proximity and functional relationship. Specifically, the weight is computed as:

𝑑𝑖𝑠𝑡2 !

(𝑝,𝑛) 2𝜎2 𝑤(𝑝,𝑛) = 𝛼(𝑝,𝑛) · exp − (3)

where 𝜎(= 0.5) is a bandwidth parameter controlling the spatial decay, 𝛼(𝑝,𝑛) quantifies the functional interaction strength between 𝑝 and 𝑛. To estimate 𝛼(𝑝,𝑛), we pretrain a POI category encoder using contrastive learning to capture task-specific functional semantics. Specifically, we treat functionally competitive POIs as positive pairs, under the assumption that POIs that share similar categories

![figure](images/Google scolar - CausalPOI_-_Spatio-Temporal_Graph-Based_Causal_Modeling_for_Cold-Start_POI_Check-in_Forecasting/img_001.png)

i ) ST-FIG Module ii) Causal Inference Module

*Figure 1: An overview structure of CausalPOI, which consists of two main components: (i) ST-FIG Module where a Spatio- Temporal Functional Interaction Graph is built for each week to capture spatial and semantic relations among POIs; and (ii)*

exhibit stronger competition. In contrast, functionally complementary POIs are considered negative pairs, reflecting weaker semantic alignment and potential cooperation. Each POI category is mapped to a textual description and encoded ultilizing BERT [4], trained with the information noise contrastive estimation (InfoNCE) [17] loss:

𝐵 ∑︁ log exp(sim(E𝑖, E+ 𝑖 )/⊔) Í𝐵 L𝐶𝐿 = − 1 (4)

𝐵 𝑗=1 exp(sim(E𝑖, E+ 𝑗 )/⊔)

𝑖=1 where 𝐵 is the mini-batch size, ⊔(= 0.5) is a temperature hyperparameter and E𝑖 and E+ 𝑖 are the embeddings of the 𝑖-th anchor and its corresponding positive sample, respectively. All embeddings are derived from POI category descriptions using a pretrained BERT encoder. For each anchor, the remaining positive samples {E+ 𝑗 | 𝑗 ≠ 𝑖} within the batch are treated as negative samples. After training, we define the functional dissimilarity between a newly added POI 𝑝 and its neighbour 𝑛 as:

𝑠(𝑝,𝑛) = − E𝑝 · E𝑛 |E𝑝| · |E𝑛| (5)

where E𝑝 and E𝑛 denote the category embeddings of POI 𝑝 and POI 𝑛 obtained from the pretrained encoder, respectively. This negated cosine similarity ensures that functionally complementary POIs—those with low semantic similarity—receive higher similarity scores, while competitive POIs—those with high semantic similarity—are assigned lower scores. We then normalize this value to the [0, 1] range to compute the functional influence weight:

𝛼(𝑝,𝑛) = 1 + 𝑠(𝑝,𝑛)

2 (6)

### 4.2 Causal Inference Module

To explicitly reason about interventions, we adopt a networked potential outcome framework with partial interference, where the exposure of each target POI depends on the configuration of its spatially adjacent POIs. The binary treatment indicator 𝑡 ∈{0, 1} denotes whether a POI is newly introduced, while aggregated neighbour influences are modeled as exposure variables summarizing nearby treatments and contexts. Within this framework, conventional predictive models—which focus mainly on correlation—often fail to disentangle causal effects, especially when assessing how a newly added POI affects and is affected by surrounding check-in dynamics. To bridge this gap, we introduce a dedicated Causal Inference Module, which is designed to estimate the ITE of a newly added POI by explicitly modeling the counterfactual scenario in which the POI had not been introduced.

4.2.1 Causal Effect Formulation. Unlike traditional causal estimation settings, our goal is to forecast the post-introduction check-in dynamics of a new POI rather than infer a population-level treatment effect. We therefore adopt a localized interference assumption, where the influence of an added POI is constrained within its 1hop spatial neighbourhood, and interference beyond this range is assumed negligible. This allows us to approximate the counterfactual outcome (absence of the POI) by constructing a control graph with preserved topology but masked semantics. Conditional on spatial and semantic covariates captured by the ST-FIG, the model learns to distinguish true causal influence from spurious correlations, yielding identifiable and interpretable representations for forecasting. We acknowledge that site selection can be endogenous because unobserved intent-to-open factors may influence both POI introduction and future demand. Our framework partially mitigates this issue by conditioning on rich pre-treatment local context and comparing treatment and control outcomes under aligned spatial topology. Nevertheless, unobserved confounders cannot be fully captured in the observational setting, and thus the estimated causal effects should be interpreted as localized counterfactual estimates rather than fully randomized intervention effects.

Concretely, the model generates two parallel predictions for a newly introduced POI 𝑝: 𝑦ˆ1 under the treatment condition, where the semantic influence of 𝑝 is present, and 𝑦ˆ0 under the control condition, where such influence is removed while preserving the same spatial topology. The contrast between these two predictions provides a counterfactual perspective on the functional impact of 𝑝, without explicitly optimizing individual treatment effects as supervised targets.

To achieve unbiased estimation, the treatment propensity score is defined solely over pre-treatment covariates. We extract a shared pre-treatment embedding E0 from the ST-FIG encoder to represent the contextual environment of 𝑝:

  h𝑝 , hN , hpos  E0 = LayerNorm concat (7)

𝑝 where h𝑝 denotes a zero embedding of the target POI, hN is the mean-pooled representation of its neighbour POIs and hpos 𝑝 is the positional encoding of location 𝑝 (defined later in Section 4.2.3).

To estimate the treatment propensity score, we apply a linear classifier over the shared representation obtained from the temporal graph encoder:

𝑝ˆ = 𝛿  W𝑝 · E0  (8) where W𝑝 is a learnable projection and 𝛿(·) denotes the sigmoid activation.

4.2.2 Treatment and Control Graph Construction. To support this estimation, we construct a pair of structurally aligned spatio-temporal graphs for each POI: • Treatment Graph (G(1)): A 1-hop subgraph centered around the target POI 𝑝, incorporating its spatial neighbours. Each node is initialized with its semantic representation. • Control Graph (G(0)): Shares the same topology as G(1), but replaces the embedding of the target POI with a zero vector, effectively simulating the absence of 𝑝 without altering the graph structure. We adopt this feature-masking strategy instead of physically removing the target POI node. Although zero-feature masking is not strictly equivalent to physically removing the target POI, it provides a structure-preserving approximation of the counterfactual scenario by suppressing the semantic influence of the target POI while keeping the local topology aligned between treatment and control graphs. In contrast, directly removing the target node would alter the neighbourhood structure, eliminate its incident edges in the 1-hop subgraph, and introduce structural mismatch. As a result, the treatment-control difference could partly reflect topology changes rather than the semantic effect of the newly introduced POI. By preserving the graph topology, our design maintains structural consistency and enables more reliable counterfactual estimation.

To mitigate potential spillover effects while maintaining comparable relational structure, the control graph keeps neighbour embeddings unchanged and preserves spatial connectivity, but removes the functional interaction term 𝛼(𝑝,𝑛) in its edge computation:

𝑑𝑖𝑠𝑡2 !

(𝑝,𝑛) 2𝜎2 𝑤(0)

− (𝑝,𝑛) = exp (9)

This design preserves the geographic topology while nullifying semantic effects, thus representing a counterfactual scenario where the target POI exerts no functional impact on its neighbours. For numerical stability, all adjacency weights are locally normalized such that Í 𝑛∈𝑁 (𝑝) 𝑤˜ (𝑝,𝑛) = 1, and the normalized 𝑤˜ (𝑝,𝑛) is used as the attention bias in the GATv2 encoder for both graphs.

4.2.3 Feature Extraction. To capture both spatial and temporal context, we construct a sequence of weekly graphs over W consecutive weeks. Each weekly graph G(𝑡)

𝑤 represents the 1-hop neighbourhood of POI 𝑝 at week w under treatment condition 𝑡 ∈{0, 1}. Unlike static spatial graphs, both the node features and neighbourhood sets are time-varying, reflecting changes in active POIs and week-specific check-in dynamics. The neighbour set Nw(𝑝) is dynamically updated to include only POIs that remain active during week w, allowing local connectivity to evolve over time.

We use GATv2 [2] as the shared graph encoder for each weekly graph. This choice is motivated by the localized 1-hop structure of ST-FIG, where the key challenge is not deep multi-hop propagation, but edge-aware relation modeling between the target POI and its heterogeneous neighbours. Unlike Transformer or Set Attention, which mainly treat neighbouring POIs as unordered tokens and KDD ’26, August 09–13, 2026, Jeju Island, Republic of Korea Zhaoqi Zhang et al.

rely on content-based attention, GATv2 naturally supports message passing with edge attributes. Therefore, we incorporate the scalar edge weight as an edge attribute to directly influence the attention computation, serving as a scaling factor that adjusts the importance of neighbour messages according to their spatial-functional affinities:

H(𝑡)

𝑤 = GATv2 (G(𝑡)

𝑤 ) ∈ R(𝑁+1)×4𝑑 (10) where 𝑁 denotes the number of neighbour nodes, including the target POI and its spatial neighbours, and 𝑑 (= 128) is the embedding dimension. From this matrix, we extract the embedding of the central node h(𝑡)

𝑝,w, corresponding to the target POI 𝑝, and compute the average embedding of its neighbours:

N,w = 1 |𝑁 | h(𝑡)

h(𝑡)

∑︁ 𝑛,w (11)

𝑛∈𝑁 To incorporate geographic information, we encode the latitude and longitude of each POI using a sinusoidal position encoding scheme that integrates multiple frequency components across dimensions, enabling the representation to capture spatial information at varying levels of granularity. Specifically, for each coordinate 𝑝.𝑔 ∈{lat𝑝, lon𝑝} , the 𝑖-th dimension of its encoding is defined as:

𝜆 · 𝑝𝑐 · 10000− 2𝑘   if 𝑖 = 2𝑘 sin   𝑑 PE(𝑖) (𝑝.𝑔) = ∀𝑝𝑐 ∈ 𝑝.𝑔 𝜆 · 𝑝𝑐 · 10000− 2𝑘   if 𝑖 = 2𝑘 + 1 cos 𝑑 (12) where 𝑑 (= 128) denotes the dimensionality of the positional encoding, and 𝜆 (= 100) is a scaling factor designed to improve the sensitivity to subtle spatial variations among POIs based on their geographic coordinates. The encodings of the latitude and longitude are concatenated to form the final positional embedding hpos:

𝑝 = Concat  PE(lat𝑝), PE(lon𝑝) ∈ R2𝑑 (13)

hpos These three components are concatenated and passed through a LayerNorm layer to yield a unified representation for week w:

E(𝑡)

h(𝑡)

𝑝,w , h(𝑡)

 h i N,w , hpos w = LayerNorm concat (14)

𝑝 The vectors is then fed into a GRU to capture temporal dynamics:

E(𝑡) = GRU([E(𝑡)

1 , . . . , E(𝑡) W ]) (15)

This final representation E(𝑡) is then used to predict counterfactual check-in sequences under both treatment and control conditions via the causal prediction module.

4.2.4 Causal Prediction. The temporally aggregated representation E(𝑡) encodes both the evolving local interaction context and the geographic characteristics of POI 𝑝 under treatment condition 𝑡. To enable counterfactual outcome modeling, we adopt a treatment-aware prediction head that maps E(𝑡) to a sequence of weekly check-in predictions. This design allows the model to generate both factual and counterfactual outcome trajectories while maintaining structural alignment between treatment and control representations. Specifically, E(𝑡) is fed into two outcome decoders corresponding to treatment and control conditions, respectively:

yˆ𝑡 = 𝑓𝑡 (E(𝑡)) ∈ R𝑊 , 𝑡 ∈{0, 1} (16)

where 𝑓1(·) and 𝑓0(·) are parameter-shared temporal decoders with treatment-specific output heads.

### 4.3 Training Loss

The model is trained using the following temporally extended loss:

𝑛 ∑︁ "

W ∑︁ L𝑇𝐶 = 1 1 W 2 𝑦ˆ(𝑖)

𝑡,w − 𝑦(𝑖)

 w 𝑛 𝑖=1 𝑤=1 (17)

𝑝ˆ(𝑖),𝑡(𝑖) #  + 𝛾 · CrossEntropy , 𝑡,w = 𝑡(𝑖) · 𝑦ˆ(𝑖)

𝑦ˆ(𝑖)

1,w + (1 − 𝑡(𝑖)) · 𝑦ˆ(𝑖) 0,w (18)

where 𝑦ˆ(𝑖)

𝑡,w is the predicted outcome at week w under the observed treatment 𝑡(𝑖) ∈{0, 1}, and 𝛾(= 0.2) is a hyperparameter that balances the prediction and treatment components.

## 5 Experiments

To evaluate the effectiveness of CausalPOI, we conduct experiments on four real-world datasets and compare it with established baseline methods. We further perform an ablation study to analyze the contribution of each key component to the overall performance gains. In addition, we conduct parameter sensitivity analysis to examine the robustness of CausalPOI under different hyperparameter settings. Finally, we validate the reliability of the estimated causal effects through an uplift sanity check and a placebo test, which help verify whether the learned effects are meaningful.

### 5.1 Experimental Setups

5.1.1 Datasets. In our data collection process, we download POI data and user check-in data from SafeGraph 2. We divide the dataset into four regions, Northeast, Midwest, South, and West, following the American official region segmentation. The data covers the period from Sep 2018 to Jan 2020, which corresponds to exactly 74 consecutive weeks. As part of our experimental design, we define newly added POIs as those that emerged within the observation window and persisted for at least 40 weeks. We focus on predicting the weekly check-in volumes for the first four weeks after each new POI’s introduction. The statistics are summarized in Table 1.

*Table 1: Statistics of datasets*

Region Census POI Added POI Northeast 42,438 998,379 16,959 Midwest 52,894 1,209,427 19,116 South 75,469 2,156,091 31,894 West 46,938 1,453,062 21,611 5.1.2 Baselines. We compare CausalPOI with eleven strong baselines, including four time-series GNN-based models [1, 10, 25, 29], one node-update-based model [3], two statistical-based models [16, 20], two large language model (LLM)-based approaches [8, 12], one causal-based model [34] and one generative synthesis-based model [22]. Details of the baselines can be found in Appendix B.

Our task focuses on the cold-start scenario, where a newly added POI has no historical check-in records available at prediction time. This poses challenges for baseline models that rely on temporal 2https://www.safegraph.com

*Table 2: Estimation and ablation study of cold-start POI check-in forecasting. We evaluate model performance using Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE). The row highlighted in bold represents the performance of CausalPOI, while the rows above it show the baseline models. Based on their underlying approach, we categorize the baselines into six types: time-series GNN-based (G), node-update-based (N), statistical-based (S), LLM-based (L), causal-based (C) and generative synthesis-based (D). The lower part of the table presents the results of the ablation study. To ensure robustness, all metrics are reported as the mean and standard deviation over ten independent runs.*

Type Model Northeast Midwest South West RMSE ↓ MAE ↓ RMSE ↓ MAE ↓ RMSE ↓ MAE ↓ RMSE ↓ MAE ↓ G DCRNN 19.86 4.65 22.40 (± 0.36)

(± 0.26)

(± 0.40)

G GraphWaveNet 18.62 4.41 20.87 (± 0.32)

(± 0.24)

(± 0.36)

G AGCRN 17.10 4.08 19.25 (± 0.28)

(± 0.22)

(± 0.31)

G LightST 15.72 3.58 17.66 (± 0.30)

(± 0.18)

(± 0.32)

D TrafficStream 14.96 3.46 16.98 (± 0.27)

(± 0.17)

(± 0.30)

S SVGP 15.40 3.25 18.30 (± 0.05)

(± 0.13)

(± 0.04)

S LCFM 12.82 2.90 15.88 (± 0.03)

(± 0.14)

(± 0.01)

L TIME-LLM 9.67 2.08 11.83 (± 0.04)

(± 0.11)

(± 0.03)

L TimeCMA 8.88 1.93 10.98 (± 0.06)

(± 0.10)

(± 0.05)

C GCIM 7.68 2.05 8.34 (± 0.10)

(± 0.08)

(± 0.11)

N KGDiff 6.74 1.93 7.29 (± 0.09)

(± 0.07)

(± 0.10)

- CausalPOI 5.36 1.84 5.87 (± 0.55)

(± 0.06)

(± 0.38)

w/o ST-FIG Module 5.89 1.94 6.19 (± 0.60)

(± 0.07)

(± 0.42)

w/o Causal Module 5.90 1.92 6.13 (± 0.44)

(± 0.04)

(± 0.57)

w/o Propensity Score 5.48 1.88 6.02 (± 0.49)

(± 0.04)

(± 0.31)

sequences. To enable a practical and model-compatible comparison, we tailor the input configurations according to the intrinsic requirements of each model type. For statistical and LLM-based baselines, which do not rely on temporal behavioural signals, we use only static semantic features. For GNN-based baselines, which require temporal input sequences, we construct a proxy temporal input for each cold-start POI by aggregating check-in records from its spatial neighbours within a predefined radius 𝑚𝑎𝑥𝑑𝑖𝑠𝑡. Specifically, we first compute a neighbourhood-level activity signal by averaging the historical check-ins of neighbouring POIs over several preceding time windows. Since cold-start POIs typically exhibit very low initial activity, directly assigning the neighbour-averaged signal would substantially overestimate their early-stage check-in volumes. To address this issue, we introduce a cold-start attenuation 5.18 23.35 5.39 24.52 5.56 (± 0.30)

(± 0.38)

(± 0.28)

(± 0.35)

(± 0.27)

4.93 21.83 5.16 23.07 5.31 (± 0.27)

(± 0.35)

(± 0.26)

(± 0.33)

(± 0.25)

4.59 20.14 4.81 21.36 4.97 (± 0.24)

(± 0.30)

(± 0.23)

(± 0.29)

(± 0.23)

4.02 18.48 4.25 19.61 4.38 (± 0.19)

(± 0.38)

(± 0.23)

(± 0.33)

(± 0.26)

3.90 17.84 4.12 18.97 4.26 (± 0.18)

(± 0.33)

(± 0.21)

(± 0.31)

(± 0.20)

4.20 20.80 4.48 22.30 4.79 (± 0.14)

(± 0.04)

(± 0.16)

(± 0.03)

(± 0.15)

3.77 17.92 3.98 19.60 4.08 (± 0.15)

(± 0.01)

(± 0.15)

(± 0.01)

(± 0.17)

2.81 14.06 2.96 15.48 3.12 (± 0.11)

(± 0.04)

(± 0.11)

(± 0.03)

(± 0.12)

2.62 13.18 2.81 14.62 2.97 (± 0.09)

(± 0.07)

(± 0.12)

(± 0.06)

(± 0.11)

2.21 9.12 2.29 9.56 2.36 (± 0.09)

(± 0.12)

(± 0.09)

(± 0.10)

(± 0.10)

2.08 8.01 2.15 8.43 2.21 (± 0.07)

(± 0.11)

(± 0.08)

(± 0.09)

(± 0.08)

2.00 5.88 1.98 6.17 1.95 (± 0.05)

(± 0.49)

(± 0.05)

(± 0.55)

(± 0.09)

2.05 6.22 2.02 6.31 2.00 (± 0.07)

(± 0.50)

(± 0.08)

(± 0.40)

(± 0.06)

2.05 6.23 2.03 6.31 1.97 (± 0.07)

(± 0.50)

(± 0.07)

(± 0.28)

(± 0.04)

2.04 5.98 1.99 6.21 1.96 (± 0.05)

(± 0.20)

(± 0.04)

(± 0.42)

(± 0.05)

factor 𝜔 ∈(0, 1) and scale the neighbourhood-level activity signal accordingly. The attenuation factor 𝜔 is determined using training data only and is defined as a single global scalar, rather than a category-specific or region-specific coefficient. Specifically, we first examine cold-start POIs in the training set and compute their average check-in volume over the initial time windows after introduction, which characterizes typical early-stage cold-start activity. In parallel, we compute the corresponding neighbourhood-level activity signal by averaging the check-in volumes of their spatial neighbours over the same time windows. The attenuation factor 𝜔 is then calibrated to align the magnitude of the neighbourhoodlevel activity signal with the average early-stage cold-start activity. This training-only calibration prevents information leakage from validation or test data while providing a fair proxy temporal input KDD ’26, August 09–13, 2026, Jeju Island, Republic of Korea Zhaoqi Zhang et al.

for baselines that require historical sequences. The scaled sequence is used as the proxy temporal input for the target cold-start POI in GNN-based baselines, while neighbouring nodes use their actual historical check-in sequences or temporally aggregated versions when required by the baseline implementation. A spatial subgraph containing the target POI and its neighbours is then fed into the GNN encoder, and the output representation of the target POI node is used for prediction.

5.1.3 Experimental Settings. The model is trained until convergence with a learning rate of 3e-4, a batch size of 32. We utilize the bert-base-uncased model with a hidden size of 768 to encode textual information. All the experiments involving deep learning frameworks are executed on a V100-SXM2 GPU.

### 5.2 Performance Analysis

As shown in Table 2, the experimental results demonstrate clear and consistent performance differences among the baseline methods, highlighting their distinct capabilities in handling the cold-start POI check-in forecasting task.

Time-series GNN-based models exhibit the weakest performance across all regions. Although pseudo temporal sequences can be constructed from neighboring POIs under cold-start settings, such approximations introduce substantial noise and fail to capture true behavioral dynamics. Moreover, these models fundamentally rely on historical activity signals and lack mechanisms to incorporate semantic or functional attributes, making it difficult to distinguish functionally different POIs with similar spatial neighborhoods. Statistical-based approaches achieve moderate improvements by incorporating static spatial features. SVGP models spatial influence through distance-based kernels, while LCFM captures latent flows among POIs, highlighting the importance of inter-POI dependencies. However, both methods rely on coarse spatial representations and do not explicitly encode local graph structures, limiting their expressiveness in fine-grained spatial contexts. LLM-based methods substantially outperform the above baselines by leveraging rich textual descriptions to learn discriminative semantic representations, enabling strong generalization under cold-start conditions. Nevertheless, they primarily operate at the semantic level and do not explicitly model spatial proximity or neighborhood interactions. Among the additional closely related baselines, Traffic- Stream performs better than time-series GNN models, suggesting that modeling evolving graph structures is helpful under cold-start settings. GCIM and KGDiff further achieve stronger results, indicating the potential benefits of causal spatio-temporal modeling and generative synthesis for unseen nodes. However, these methods still underperform CausalPOI because they are not specifically designed for localized POI-level intervention-aware forecasting or structure-aligned treatment-control comparison. In particular, GCIM mainly focuses on causal representation learning over spatiotemporal structures, while KGDiff emphasizes generating plausible sequences for unseen nodes.

In contrast, CausalPOI consistently achieves the best performance across all regions and metrics. By constructing a local spatial graph centered on the target POI and integrating semantic attributes within a unified causal framework, CausalPOI jointly captures spatial structure and functional semantics, leading to significant performance gains over all competing methods.

### 5.3 Ablation Study

To evaluate the effectiveness of key components in the CausalPOI framework, we conduct ablation experiments by selectively removing the ST-FIG and the Causal Model.

*Table 2 reports the ablation results of the proposed CausalPOI framework across four regions. Overall, removing either the ST-FIG module or the causal inference module leads to consistent perfor- mance degradation in terms of both RMSE and MAE, indicating their respective contributions to the model’s overall effectiveness. Removing the ST-FIG module results in noticeable performance drops across all regions. Similar degradations are observed in the Midwest, South, and West datasets. This confirms that explicitly modeling functional interactions among neighbouring POIs is cru- cial. By incorporating semantics-aware interaction strengths into the graph structure, ST-FIG enables the GNN encoder to distin- guish functionally relevant neighbours from purely spatially proxi- mate ones, leading to more informative local representations for cold-start forecasting. Removing the causal inference module also consistently degrades performance. This demonstrates that purely predictive modeling is insufficient for estimating the incremental impact of newly introduced POIs under interference. By construct- ing aligned treatment and control graphs and explicitly modeling counterfactual outcomes, the causal module allows CausalPOI to disentangle genuine treatment effects from correlated neighbour- hood dynamics. In addition, we analyze the effect of the propensity loss by setting𝛾 = 0, which corresponds to removing the propensity term from the training objective. As shown in Table 2, removing the propensity loss leads to a small but consistent performance degradation across all four regions. Although the magnitude of degradation is smaller compared to removing the ST-FIG or the causal inference module, the results indicate that the propensity loss provides a stabilizing effect during training. Specifically, it acts as an auxiliary regularizer that encourages balanced representa- tions between treatment and control branches, leading to slightly improved forecasting performance.*

### 5.4 Parameters Analysis

We evaluate the sensitivity of CausalPOI to three key hyperparameters: the causal loss weight 𝛾, the spatial decay bandwidth 𝜎, and the maximum neighbourhood distance max𝑑𝑖𝑠𝑡, which respectively control the strength of causal regularization, the attenuation rate of spatial influence in graph construction, and the spatial extent of local neighbourhood graphs. As shown in Figure 2, the selected parameter configuration achieves the best overall performance across all regions. A too-small value of 𝛾 weakens the effect of treatment prediction, while an overly large one leads to over-regularization. An overly small 𝜎 cause spatial influence to decay too rapidly, restricting effective information propagation within local neighbourhoods and reducing the benefit of graph-based modelling, whereas an excessively large 𝜎 over-smooth spatial influence across distant POIs, diluting locality-aware signals and introducing irrelevant spatial dependencies. Similarly, a too-small 𝑚𝑎𝑥𝑑𝑖𝑠𝑡 restricts the

![figure](images/Google scolar - CausalPOI_-_Spatio-Temporal_Graph-Based_Causal_Modeling_for_Cold-Start_POI_Check-in_Forecasting/img_002.png)

*Figure 2: Parameter sensitivity analysis of CausalPOIs.*

![figure](images/Google scolar - CausalPOI_-_Spatio-Temporal_Graph-Based_Causal_Modeling_for_Cold-Start_POI_Check-in_Forecasting/img_003.png)

*Figure 3: Sanity check of estimated uplift of CausalPOI.*

spatial coverage of local graphs, while a too-large value introduces noisy and less relevant neighbours.

### 5.5 Uplift Sanity Check

Beyond predictive accuracy, we assess whether the estimated uplift exhibits reasonable behavior under different urban contexts. Since ground-truth causal effects are unavailable, we conduct sanity checks to evaluate the plausibility of the estimated counterfactual outcomes. We perform a group-level analysis by comparing the distributions of relative uplift across cold-start POIs under different levels of neighborhood competition. For each POI, we quantify competition by computing the average functional similarity between the POI and its surrounding neighboring POIs, based on semantic embeddings. POIs in the test set of our four datasets are then ranked by this competition score and partitioned into high- and low-competition groups using the top and bottom 20% quantiles,

*Table 3: Placebo test results of CausalPOI.*

Region Real Int. Placebo Int. Shifted Int.

Northeast 0.228 0.013 0.171 Midwest 0.241 0.015 0.179 South 0.257 0.018 0.174 West 0.249 0.016 0.173 respectively. As shown in Figure 3, POIs in highly competitive environments exhibit consistently smaller relative uplift than those in less competitive settings, which is directionally consistent with urban economic intuition.

### 5.6 Placebo Tests

To further examine whether the estimated uplift is interventionspecific, we conduct placebo tests under pseudo and shifted intervention settings. As shown in Table 3, the real intervention setting yields consistently larger uplift values across all regions, ranging from 0.228 to 0.257. In contrast, randomly assigning pseudointroduction events to non-new POIs leads to near-zero uplift values, ranging from 0.013 to 0.018. This indicates that the model does not assign large treatment effects to arbitrary POIs. When the true introduction week is shifted by approximately four weeks, the estimated uplift also decreases from 0.057 to 0.083 compared with the real intervention setting. These results suggest that the learned uplift is tied to the actual POI introduction event and its timing.

## 6 Conclusions

This paper presents a novel problem – cold-start POI check-in forecasting, which aims to predict the future check-in pattern of a newly introduced POI, by modeling its temporal evolution and functional interactions with nearby POIs in a structured urban spatial context. To address this challenge, we propose CausalPOI, a spatio-temporal causal representation learning framework that constructs structurally aligned treatment and control graphs to simulate factual and counterfactual outcomes. By introducing the Functional Interaction Graph and leveraging contrastive pretraining, our approach effectively captures both spatial proximity and latent functional semantics among POIs. This design enables precise individual treatment effect estimation and improves predictive performance in POI-level forecasting tasks. Through extensive experiments on real-world datasets, CausalPOI demonstrates strong performance in modeling fine-grained POI dynamics and offers actionable insights for urban planning and intervention analysis.

## Acknowledgments

This research is supported by the National Research Foundation, Singapore, under its Frontier CRP Grant (NRF-F-CRP-2024-0005), and under its AI Singapore Programme (AISG Award No: AISG3-RP- 2024-034). This research is also supported by NTU SUG-NAP. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not reflect the views of the National Research Foundation, Singapore. This work is also supported by the China Agricultural University "Young Researcher" Start-up Fund No. QNYJY2024144 and the Visiting Scholar Program of the China Scholarship Council (CSC) No. 202506350123.

KDD ’26, August 09–13, 2026, Jeju Island, Republic of Korea Zhaoqi Zhang et al.

## References

[1] Lei Bai, Lina Yao, Can Li, Xianzhi Wang, and Can Wang. 2020. Adaptive graph convolutional recurrent network for traffic forecasting. Advances in neural information processing systems 33 (2020), 17804–17815. [2] Shaked Brody, Uri Alon, and Eran Yahav. 2021. How attentive are graph attention networks? arXiv preprint arXiv:2105.14491 (2021). [3] Xu Chen, Junshan Wang, and Kunqing Xie. 2021. TrafficStream: A streaming traffic flow forecasting framework based on graph neural networks and continual learning. arXiv preprint arXiv:2106.06273 (2021). [4] Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2018. Bert:

Pre-training of deep bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805 (2018). [5] Yanjie Fu, Pengyang Wang, Jiadi Du, Le Wu, and Xiaolin Li. 2019. Efficient region embedding with multi-view spatial networks: A perspective of localityconstrained spatial autocorrelations. In Proceedings of the AAAI conference on artificial intelligence, Vol. 33. 906–913. [6] Shengnan Guo, Youfang Lin, Ning Feng, Chao Song, and Huaiyu Wan. 2019.

Attention based spatial-temporal graph convolutional networks for traffic flow forecasting. In Proceedings of the AAAI conference on artificial intelligence, Vol. 33. 922–929. [7] Arash Hajisafi, Haowen Lin, Sina Shaham, Haoji Hu, Maria Despoina Siampou, Yao-Yi Chiang, and Cyrus Shahabi. 2023. Learning dynamic graphs from all contextual information for accurate point-of-interest visit forecasting. In Proceedings of the 31st ACM International Conference on Advances in Geographic Information Systems. 1–12. [8] Ming Jin, Shiyu Wang, Lintao Ma, Zhixuan Chu, James Y Zhang, Xiaoming Shi, Pin-Yu Chen, Yuxuan Liang, Yuan-Fang Li, Shirui Pan, et al. 2023. Time-llm: Time series forecasting by reprogramming large language models. arXiv preprint arXiv:2310.01728 (2023). [9] Shuangli Li, Jingbo Zhou, Tong Xu, Hao Liu, Xinjiang Lu, and Hui Xiong. 2020.

Competitive analysis for points of interest. In Proceedings of the 26th ACM SIGKDD international conference on knowledge discovery & data mining. 1265–1274. [10] Yaguang Li, Rose Yu, Cyrus Shahabi, and Yan Liu. 2017. Diffusion convolutional recurrent neural network: Data-driven traffic forecasting. arXiv preprint arXiv:1707.01926 (2017). [11] Ziyao Li, Shang-Ling Hsu, and Cyrus Shahabi. 2024. Forecasting Unseen Points of Interest Visits Using Context and Proximity Priors. In 2024 IEEE International Conference on Big Data (BigData). IEEE, 5812–5818. [12] Chenxi Liu, Qianxiong Xu, Hao Miao, Sun Yang, Lingzheng Zhang, Cheng Long, Ziyue Li, and Rui Zhao. 2025. Timecma: Towards llm-empowered multivariate time series forecasting via cross-modality alignment. In Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 39. 18780–18788. [13] Jia Liu, Tianrui Li, Shenggong Ji, Peng Xie, Shengdong Du, Fei Teng, and Junbo Zhang. 2021. Urban flow pattern mining based on multi-source heterogeneous data fusion and knowledge graph embedding. IEEE Transactions on Knowledge and Data Engineering 35, 2 (2021), 2133–2146. [14] Ruoqi Liu, Changchang Yin, and Ping Zhang. 2020. Estimating individual treatment effects with time-varying confounders. In 2020 IEEE international conference on data mining (ICDM). IEEE, 382–391. [15] Jing Ma, Mengting Wan, Longqi Yang, Jundong Li, Brent Hecht, and Jaime Teevan.

2022. Learning causal effects on hypergraphs. In Proceedings of the 28th ACM SIGKDD Conference on Knowledge Discovery and Data Mining. 1202–1212. [16] Christof Naumzik, Patrick Zoechbauer, and Stefan Feuerriegel. 2020. Mining points-of-interest for explaining urban phenomena: A scalable variational inference approach. In Proceedings of The Web Conference 2020. 2342–2353. [17] Aaron van den Oord, Yazhe Li, and Oriol Vinyals. 2018. Representation learning with contrastive predictive coding. arXiv preprint arXiv:1807.03748 (2018). [18] Uri Shalit, Fredrik D Johansson, and David Sontag. 2017. Estimating individual treatment effect: generalization bounds and algorithms. In International conference on machine learning. PMLR, 3076–3085. [19] Claudia Shi, David Blei, and Victor Veitch. 2019. Adapting neural networks for the estimation of treatment effects. Advances in neural information processing systems 32 (2019). [20] Daniel Tschernutter and Stefan Feuerriegel. 2021. A latent customer flow model for interpretable predictions of check-in counts. In 2021 IEEE International Conference on Big Data (Big Data). IEEE, 529–539. [21] Lijing Wang, Aniruddha Adiga, Jiangzhuo Chen, Adam Sadilek, Srinivasan Venkatramanan, and Madhav Marathe. 2022. Causalgnn: Causal-based graph neural networks for spatio-temporal epidemic forecasting. In Proceedings of the AAAI conference on artificial intelligence, Vol. 36. 12191–12199. [22] Zi’ang Wang, Lei Chen, Yuanchang Jin, Pan Deng, Shuangshuang Pang, Junting Liu, and Yu Zhao. 2026. Knowledge Graph Guided Heterogeneity-Informed Diffusion Model for Spatio-Temporal Generation. In Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 40. 15915–15923. [23] Shangbin Wu, Xu Yan, Xiaoliang Fan, Shirui Pan, Shichao Zhu, Chuanpan Zheng, Ming Cheng, and Cheng Wang. 2022. Multi-graph fusion networks for urban region embedding. arXiv preprint arXiv:2201.09760 (2022).

[24] Zonghan Wu, Shirui Pan, Guodong Long, Jing Jiang, Xiaojun Chang, and Chengqi Zhang. 2020. Connecting the dots: Multivariate time series forecasting with graph neural networks. In Proceedings of the 26th ACM SIGKDD international conference on knowledge discovery & data mining. 753–763. [25] Zonghan Wu, Shirui Pan, Guodong Long, Jing Jiang, and Chengqi Zhang. 2019.

Graph wavenet for deep spatial-temporal graph modeling. arXiv preprint arXiv:1906.00121 (2019). [26] Guolei Yang, Ying Cai, and Chandan K Reddy. 2018. Recurrent spatio-temporal point process for check-in time prediction. In Proceedings of the 27th ACM International Conference on Information and Knowledge Management. 2203–2211. [27] Bing Yu, Haoteng Yin, and Zhanxing Zhu. 2017. Spatio-temporal graph convolutional networks: A deep learning framework for traffic forecasting. arXiv preprint arXiv:1709.04875 (2017). [28] Shilu Yuan, Dongfeng Li, Wei Liu, Xinxin Zhang, Meng Chen, Junjie Zhang, and Yongshun Gong. 2024. Fine-Grained Urban Flow Inference with Multi-scale Representation Learning. arXiv preprint arXiv:2406.09710 (2024). [29] Qianru Zhang, Xinyi Gao, Haixin Wang, Siu Ming Yiu, and Hongzhi Yin. 2025.

Efficient traffic prediction through spatio-temporal distillation. In Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 39. 1093–1101. [30] Yunchao Zhang, Yanjie Fu, Pengyang Wang, Xiaolin Li, and Yu Zheng. 2019.

Unifying inter-region autocorrelation and intra-region structures for spatial embedding via collective adversarial learning. In Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining. 1700– 1708. [31] Yu Zhang, Yonghui Xu, Lizhen Cui, and Zhongmin Yan. 2023. Multi-view graph contrastive learning for urban region representation. In 2023 International Joint Conference on Neural Networks (IJCNN). IEEE, 1–8. [32] Zhaoqi Zhang, Pasquale Balsebre, Siqiang Luo, Zhen Hai, and Jiangping Huang.

2024. StructAM: Enhancing Address Matching through Semantic Understanding of Structure-aware Information. In Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024). 15350–15361. [33] Zhaoqi Zhang, Miao Xie, Pasquale Balsebre, Weiming Huang, Siqiang Luo, and Gao Cong. 2026. UrbanMFM: Spatial Graph-Based Multiscale Foundation Models for Learning Generalized Urban Representation. IEEE Transactions on Knowledge and Data Engineering (2026). [34] Yu Zhao, Pan Deng, Junting Liu, Xiaofeng Jia, and Jianwei Zhang. 2023. Generative causal interpretation model for spatio-temporal representation learning. In Proceedings of the 29th ACM SIGKDD Conference on Knowledge Discovery and Data Mining. 3537–3548.

## A Data Example

We hereby provide data examples of POI and check-in sequence in Table 4.

## B Baselines

- DCRNN [10] models spatiotemporal dependencies using bidirectional diffusion convolution on directed graphs and GRU-based sequence-to-sequence learning, with scheduled sampling to stabilize multi-step forecasting. • GraphWaveNet [25] combines dilated causal convolutions with adaptive graph convolution, learning a self-adjusting adjacency matrix to model latent spatial dependencies and capture longrange temporal patterns. • AGCRN [1] introduces node-specific adaptive adjacency matrices and gated recurrent units, enabling flexible modeling of heterogeneous spatial-temporal correlations without fixed graph structures. • LightST [29] is a lightweight spatio-temporal graph neural network that improves forecasting efficiency via spatio-temporal distillation while maintaining competitive accuracy. • TrafficStream [3] focuses on spatio-temporal prediction under node updates, using graph neural networks and continual learning to handle streaming traffic data with dynamically evolving nodes.

*Table 4: Examples of POI and POI check-in sequence*

- SVGP [16] uses a sparse Gaussian process to model urban phenomena based on POI distributions, capturing spatial effects through distance-based kernels with interpretable outputs. • LCFM [20] Explains POI check-ins through latent customer flows, including direct visits, competition, and transitions, using a fixedpoint formulation and Gaussian processes for interpretable spatial modelling. • TIME-LLM [8] reprograms LLMs for time series forecasting via prompts, achieving strong performance without fine-tuning model weights. • TimeCMA [12] is a recent LLM-based time series forecasting method that enhances prediction by modeling cross-variable temporal dependencies through contextual representations. • GCIM [34] belongs to causal spatio-temporal intervention modeling, aiming to learn interpretable spatio-temporal representations through generative causal mechanisms. • KGDiff[22] is a generative synthesis-based method that leverages knowledge graphs and diffusion modeling to capture heterogeneity and generate spatio-temporal sequences.

Type Example POI id : sg:002a9...bc48e, category : Grocery Stores, lat : 44.556128, lon : -123.066371, tags : { name : Jacksons Food Stores, street : 33157 Highway 34 SE, city : Albany, state : OR, postcode : 97322 } check-in seq id : sg:1e57c...2318f, category : Grocery Stores, lat : 18.465922, lon : -66.10359, sequence : [ 2018-09-08 to 2018-09-14: 2, 2018-09-15 to 2018-09-21: 1, ... 2020-01-25 to 2020-01-31: 2 ]
