# 選擇地形｜雙軸取捨試驗（非正式推薦）

來源快照 2026-09-26（不是本報告日期新抓取）；來源檔 runs/2026-09-26-general-grok16/candidates.csv；AA-Intelligence-Index / AA-Intelligence-Index-v4.3.2（公開榜單版本由同日 release 跨頁推定，非榜單標示或 API envelope 證明）/ api；min-score=0（同版本全候選取捨示意；不是實用能力門檻）；eps_score=2，本版 CI 未公布，沿用規約。

**輸入 155 · 潛在取捨 21 · 被支配 134**

本試驗只移除同時不較強且不較便宜的行（至少一軸嚴格較差）。同 Score／同 Cost_adj 的不同 route 全保留；與正式 CP-new-high 階梯可刻意不同。不設 5% 效用刪除門檻，不鏈式刪除微幅升級。Claude 僅比較，不推薦。

Cost_adj = Cost_orig / 情境係數：GPT ×18（預設 ×18 源自個人約 ×18.9 實測保守取整；當次係數非實測），Grok ×16 為用戶指定情境（非實測）；Contributor ×1。這些不是實際 API 價格或 AA 實測調整價。原價證據 GRADE-B 仍有推導假設，Contributor cache-write 以一般 input 價計是未經 Meta 明確證實的關鍵假設。

ΔScore < eps_score 只標記『分差未越噪音門檻』；達門檻也不證明實務能力不同，未達也不證明能力相同。所有保留點仍完整列出。

## 全部潛在取捨（Score 降序；升級基準是緊鄰的更便宜保留價位）

| # | Identity | Score | Cost_adj $/AA task | Cost_orig $/AA task | 係數 | 證據 | 對更便宜點的升級 |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | Claude Opus 5.5 Adaptive Reasoning, Max Effort, Default Fallback AA-public published-price（Claude：僅比較） | 57.6224 | 5.98201 | 5.98201 | ×1 | A | 相較 Claude Opus 5.5 Adaptive Reasoning, Xhigh Effort, Default Fallback AA-public published-price：ΔScore +1.63502；情境成本 ×1.72935；ΔCost_adj +$2.5229/AA task；分差未越噪音門檻 |
| 2 | Claude Opus 5.5 Adaptive Reasoning, Xhigh Effort, Default Fallback AA-public published-price（Claude：僅比較） | 55.9874 | 3.45911 | 3.45911 | ×1 | A | 相較 Claude Opus 5.5 Adaptive Reasoning, High Effort, Default Fallback AA-public published-price：ΔScore +2.40415；情境成本 ×1.898；ΔCost_adj +$1.63661/AA task；分數差異達門檻 |
| 3 | Claude Opus 5.5 Adaptive Reasoning, High Effort, Default Fallback AA-public published-price（Claude：僅比較） | 53.5832 | 1.8225 | 1.8225 | ×1 | A | 相較 GPT-6 Astra max AA-public published-price：ΔScore +0.909527；情境成本 ×10.0706；ΔCost_adj +$1.64153/AA task；分差未越噪音門檻 |
| 4 | GPT-6 Astra max AA-public published-price | 52.6737 | 0.180972 | 3.2575 | ×18 | A | 相較 GPT-6 Astra xhigh AA-public published-price：ΔScore +0.287342；情境成本 ×1.41091；ΔCost_adj +$0.0527058/AA task；分差未越噪音門檻 |
| 5 | GPT-6 Astra xhigh AA-public published-price | 52.3863 | 0.128266 | 2.3088 | ×18 | A | 相較 GPT-6 Astra high AA-public published-price：ΔScore +1.46718；情境成本 ×1.33824；ΔCost_adj +$0.032419/AA task；分差未越噪音門檻 |
| 6 | GPT-6 Astra high AA-public published-price | 50.9191 | 0.0958474 | 1.72525 | ×18 | A | 相較 GPT-6 Astra medium AA-public published-price：ΔScore +1.34871；情境成本 ×1.11982；ΔCost_adj +$0.0102558/AA task；分差未越噪音門檻 |
| 7 | GPT-6 Astra medium AA-public published-price | 49.5704 | 0.0855916 | 1.54065 | ×18 | A | 相較 Muse Spark 1.3 max Meta Contributor：ΔScore +1.47813；情境成本 ×1.34254；ΔCost_adj +$0.0218383/AA task；分差未越噪音門檻 |
| 8 | Muse Spark 1.3 max Meta Contributor | 48.0923 | 0.0637534 | 0.0637534 | ×1 | B | 相較 GPT-6 Sol max AA-public published-price：ΔScore +0.564668；情境成本 ×1.08627；ΔCost_adj +$0.00506315/AA task；分差未越噪音門檻 |
| 9 | GPT-6 Sol max AA-public published-price | 47.5276 | 0.0586902 | 1.05642 | ×18 | A | 相較 GPT-6 Astra low AA-public published-price：ΔScore +1.74572；情境成本 ×1.29224；ΔCost_adj +$0.0132728/AA task；分差未越噪音門檻 |
| 10 | GPT-6 Astra low AA-public published-price | 45.7819 | 0.0454174 | 0.817514 | ×18 | A | 相較 GPT-6 Sol xhigh AA-public published-price：ΔScore +1.68095；情境成本 ×1.53698；ΔCost_adj +$0.0158676/AA task；分差未越噪音門檻 |
| 11 | GPT-6 Sol xhigh AA-public published-price | 44.101 | 0.0295498 | 0.531896 | ×18 | A | 相較 GPT-6 Sol high AA-public published-price：ΔScore +1.27942；情境成本 ×1.41978；ΔCost_adj +$0.00873687/AA task；分差未越噪音門檻 |
| 12 | GPT-6 Sol high AA-public published-price | 42.8216 | 0.0208129 | 0.374633 | ×18 | A | 相較 GPT-6 Sol medium AA-public published-price：ΔScore +3.03945；情境成本 ×1.50939；ΔCost_adj +$0.00702392/AA task；分數差異達門檻 |
| 13 | GPT-6 Sol medium AA-public published-price | 39.7821 | 0.013789 | 0.248202 | ×18 | A | 相較 GPT-5.6 Luna max AA-public published-price：ΔScore +2.45767；情境成本 ×1.39207；ΔCost_adj +$0.0038836/AA task；分數差異達門檻 |
| 14 | GPT-5.6 Luna max AA-public published-price | 37.3244 | 0.0099054 | 0.178297 | ×18 | A | 相較 GPT-6 Luna max AA-public published-price：ΔScore +0.0684553；情境成本 ×2.61836；ΔCost_adj +$0.00612235/AA task；分差未越噪音門檻 |
| 15 | GPT-6 Luna max AA-public published-price | 37.256 | 0.00378305 | 0.068095 | ×18 | A | 相較 GPT-6 Luna xhigh AA-public published-price：ΔScore +3.37139；情境成本 ×1.63263；ΔCost_adj +$0.0014659/AA task；分數差異達門檻 |
| 16 | GPT-6 Luna xhigh AA-public published-price | 33.8846 | 0.00231715 | 0.0417088 | ×18 | A | 相較 GPT-6 Luna high AA-public published-price：ΔScore +1.73635；情境成本 ×1.45735；ΔCost_adj +$0.000727173/AA task；分差未越噪音門檻 |
| 17 | GPT-6 Luna high AA-public published-price | 32.1482 | 0.00158998 | 0.0286196 | ×18 | A | 相較 GPT-6 Luna medium AA-public published-price：ΔScore +2.68628；情境成本 ×1.65876；ΔCost_adj +$0.000631447/AA task；分數差異達門檻 |
| 18 | GPT-6 Luna medium AA-public published-price | 29.462 | 0.000958533 | 0.0172536 | ×18 | A | 相較 GPT-5.6 Luna medium AA-public published-price：ΔScore +4.42608；情境成本 ×1.10614；ΔCost_adj +$9.19747e-05/AA task；分數差異達門檻 |
| 19 | GPT-5.6 Luna medium AA-public published-price | 25.0359 | 0.000866558 | 0.015598 | ×18 | A | 相較 GPT-5.6 Luna low AA-public published-price：ΔScore +4.0234；情境成本 ×1.58722；ΔCost_adj +$0.0003206/AA task；分數差異達門檻 |
| 20 | GPT-5.6 Luna low AA-public published-price | 21.0125 | 0.000545958 | 0.00982725 | ×18 | A | 相較 GPT-6 Luna low AA-public published-price：ΔScore +0.0899303；情境成本 ×2.19172；ΔCost_adj +$0.000296858/AA task；分差未越噪音門檻 |
| 21 | GPT-6 Luna low AA-public published-price | 20.9225 | 0.000249101 | 0.00448381 | ×18 | A | 最低情境成本／同價等價路線；無更便宜比較對象 |

## 被支配行（134；每行附實際支配者）

- Claude Fable 5.1 Adaptive Reasoning, Max Effort, Default Fallback AA-public published-price（Score 53.3549、Cost_adj $7.62971、Cost_orig $7.62971、GRADE A）← Claude Opus 5.5 Adaptive Reasoning, High Effort, Default Fallback AA-public published-price
- Claude Fable 5.1 Adaptive Reasoning, Xhigh Effort, Default Fallback AA-public published-price（Score 53.2033、Cost_adj $5.9783、Cost_orig $5.9783、GRADE A）← Claude Opus 5.5 Adaptive Reasoning, High Effort, Default Fallback AA-public published-price
- Claude Opus 5.5 Adaptive Reasoning, Medium Effort, Default Fallback AA-public published-price（Score 51.2435、Cost_adj $1.33601、Cost_orig $1.33601、GRADE A）← GPT-6 Astra xhigh AA-public published-price
- Claude Fable 5.1 Adaptive Reasoning, High Effort, Default Fallback AA-public published-price（Score 51.1516、Cost_adj $3.91253、Cost_orig $3.91253、GRADE A）← GPT-6 Astra xhigh AA-public published-price
- Claude Opus 5 Adaptive Reasoning, Max Effort AA-public published-price（Score 50.7771、Cost_adj $5.8584、Cost_orig $5.8584、GRADE A）← GPT-6 Astra high AA-public published-price
- Claude Opus 5 Adaptive Reasoning, Xhigh Effort AA-public published-price（Score 49.6774、Cost_adj $4.87784、Cost_orig $4.87784、GRADE A）← GPT-6 Astra high AA-public published-price
- Claude Fable 5 Adaptive Reasoning, Max Effort, Opus 4.8 Fallback AA-public published-price（Score 49.6258、Cost_adj $8.74596、Cost_orig $8.74596、GRADE A）← GPT-6 Astra high AA-public published-price
- Claude Fable 5.1 Adaptive Reasoning, Medium Effort, Default Fallback AA-public published-price（Score 48.9206、Cost_adj $2.9826、Cost_orig $2.9826、GRADE A）← GPT-6 Astra medium AA-public published-price
- Claude Opus 5 Adaptive Reasoning, High Effort AA-public published-price（Score 48.1219、Cost_adj $3.61327、Cost_orig $3.61327、GRADE A）← GPT-6 Astra medium AA-public published-price
- Muse Spark 1.3 max AA-public published-price（Score 48.0923、Cost_adj $1.60489、Cost_orig $1.60489、GRADE A）← Muse Spark 1.3 max Meta Contributor
- GPT-5.6 Sol max AA-public published-price（Score 46.9727、Cost_adj $0.11047、Cost_orig $1.98846、GRADE A）← GPT-6 Sol max AA-public published-price
- Claude Fable 5.1 Adaptive Reasoning, Low Effort, Default Fallback AA-public published-price（Score 46.8163、Cost_adj $2.37103、Cost_orig $2.37103、GRADE A）← GPT-6 Sol max AA-public published-price
- Grok 4.7 xhigh AA-public published-price（Score 46.4466、Cost_adj $0.233645、Cost_orig $3.73833、GRADE A）← GPT-6 Sol max AA-public published-price
- Grok 4.7 high AA-public published-price（Score 46.3322、Cost_adj $0.170382、Cost_orig $2.72611、GRADE A）← GPT-6 Sol max AA-public published-price
- MiMo-V2.6-Pro unspecified AA-public published-price（Score 46.3242、Cost_adj $0.133223、Cost_orig $0.133223、GRADE A）← GPT-6 Sol max AA-public published-price
- Qwen3.8 Max 0902 AA-public published-price（Score 45.4152、Cost_adj $5.40851、Cost_orig $5.40851、GRADE A）← GPT-6 Astra low AA-public published-price
- Muse Spark 1.3 xhigh Meta Contributor（Score 45.0733、Cost_adj $0.0547675、Cost_orig $0.0547675、GRADE B）← GPT-6 Astra low AA-public published-price
- Muse Spark 1.3 xhigh AA-public published-price（Score 45.0733、Cost_adj $1.36779、Cost_orig $1.36779、GRADE A）← GPT-6 Astra low AA-public published-price
- Claude Opus 5 Adaptive Reasoning, Medium Effort AA-public published-price（Score 44.8253、Cost_adj $2.18948、Cost_orig $2.18948、GRADE A）← GPT-6 Astra low AA-public published-price
- GLM-5.3 max AA-public published-price（Score 44.7774、Cost_adj $2.00564、Cost_orig $2.00564、GRADE A）← GPT-6 Astra low AA-public published-price
- Grok 4.6 high AA-public published-price（Score 44.3113、Cost_adj $0.116184、Cost_orig $1.85894、GRADE A）← GPT-6 Astra low AA-public published-price
- Grok 4.6 xhigh AA-public published-price（Score 44.1998、Cost_adj $0.145231、Cost_orig $2.32369、GRADE A）← GPT-6 Astra low AA-public published-price
- GPT-5.6 Sol xhigh AA-public published-price（Score 44.0089、Cost_adj $0.0657979、Cost_orig $1.18436、GRADE A）← GPT-6 Sol xhigh AA-public published-price
- Step 5 Preview unspecified AA-public published-price（Score 43.7343、Cost_adj $0.715523、Cost_orig $0.715523、GRADE A）← GPT-6 Sol xhigh AA-public published-price
- Kimi K3 max AA-public published-price（Score 43.5938、Cost_adj $2.00013、Cost_orig $2.00013、GRADE A）← GPT-6 Sol xhigh AA-public published-price
- Grok 4.6 medium AA-public published-price（Score 42.8363、Cost_adj $0.0935202、Cost_orig $1.49632、GRADE A）← GPT-6 Sol xhigh AA-public published-price
- GPT-5.6 Sol high AA-public published-price（Score 42.3461、Cost_adj $0.0448879、Cost_orig $0.807983、GRADE A）← GPT-6 Sol high AA-public published-price
- Claude Opus 5.5 Adaptive Reasoning, Low Effort, Default Fallback AA-public published-price（Score 42.3078、Cost_adj $0.55118、Cost_orig $0.55118、GRADE A）← GPT-6 Sol high AA-public published-price
- GPT-5.6 Terra max AA-public published-price（Score 42.0829、Cost_adj $0.0777069、Cost_orig $1.39872、GRADE A）← GPT-6 Sol high AA-public published-price
- GLM 5.3 Flash unspecified AA-public published-price（Score 41.8075、Cost_adj $0.25326、Cost_orig $0.25326、GRADE A）← GPT-6 Sol high AA-public published-price
- Claude Opus 4.8 Adaptive Reasoning, Max Effort AA-public published-price（Score 41.7899、Cost_adj $4.08098、Cost_orig $4.08098、GRADE A）← GPT-6 Sol high AA-public published-price
- Gemini 3.8 Flash high AA-public published-price（Score 40.9262、Cost_adj $1.24279、Cost_orig $1.24279、GRADE A）← GPT-6 Sol high AA-public published-price
- Qwen3.8 Max unspecified AA-public published-price（Score 40.1529、Cost_adj $2.66998、Cost_orig $2.66998、GRADE A）← GPT-6 Sol high AA-public published-price
- Qwen3.8 2.4T A95B unspecified AA-public published-price（Score 39.8862、Cost_adj $2.15592、Cost_orig $2.15592、GRADE A）← GPT-6 Sol high AA-public published-price
- Qwen3.8-Flash-Next unspecified AA-public published-price（Score 39.8223、Cost_adj $0.372176、Cost_orig $0.372176、GRADE A）← GPT-6 Sol high AA-public published-price
- Gemini 3.8 Flash medium AA-public published-price（Score 39.774、Cost_adj $0.931038、Cost_orig $0.931038、GRADE A）← GPT-6 Sol medium AA-public published-price
- Muse Spark 1.2 xhigh AA-public published-price（Score 39.5759、Cost_adj $0.974695、Cost_orig $0.974695、GRADE A）← GPT-6 Sol medium AA-public published-price
- DeepSeek V4.1 Flash Reasoning, Max Effort AA-public published-price（Score 39.4562、Cost_adj $0.265225、Cost_orig $0.265225、GRADE A）← GPT-6 Sol medium AA-public published-price
- Claude Opus 5 Adaptive Reasoning, Low Effort AA-public published-price（Score 39.3543、Cost_adj $1.0983、Cost_orig $1.0983、GRADE A）← GPT-6 Sol medium AA-public published-price
- GPT-5.6 Sol medium AA-public published-price（Score 39.2364、Cost_adj $0.0280551、Cost_orig $0.504993、GRADE A）← GPT-6 Sol medium AA-public published-price
- Gemini 3.7 Flash high AA-public published-price（Score 39.0595、Cost_adj $0.925336、Cost_orig $0.925336、GRADE A）← GPT-6 Sol medium AA-public published-price
- Grok 4.5 high AA-public published-price（Score 38.8121、Cost_adj $0.0647785、Cost_orig $1.03646、GRADE A）← GPT-6 Sol medium AA-public published-price
- GPT-5.5 xhigh AA-public published-price（Score 38.3556、Cost_adj $0.146332、Cost_orig $2.63398、GRADE A）← GPT-6 Sol medium AA-public published-price
- Claude Sonnet 5 Adaptive Reasoning, Max Effort AA-public published-price（Score 38.1639、Cost_adj $5.09116、Cost_orig $5.09116、GRADE A）← GPT-6 Sol medium AA-public published-price
- GPT-5.6 Terra xhigh AA-public published-price（Score 37.9513、Cost_adj $0.0350995、Cost_orig $0.631791、GRADE A）← GPT-6 Sol medium AA-public published-price
- GPT-5.5 high AA-public published-price（Score 36.9794、Cost_adj $0.0856272、Cost_orig $1.54129、GRADE A）← GPT-6 Luna max AA-public published-price
- DeepSeek V4 Pro 0813 Reasoning, Max Effort AA-public published-price（Score 35.9968、Cost_adj $0.674022、Cost_orig $0.674022、GRADE A）← GPT-6 Luna max AA-public published-price
- Grok 4.6 low AA-public published-price（Score 35.1247、Cost_adj $0.0297053、Cost_orig $0.475285、GRADE A）← GPT-6 Luna max AA-public published-price
- DeepSeek V4 Flash Vision Reasoning, Max Effort AA-public published-price（Score 34.8391、Cost_adj $0.314372、Cost_orig $0.314372、GRADE A）← GPT-6 Luna max AA-public published-price
- GPT-5.6 Luna xhigh AA-public published-price（Score 34.5553、Cost_adj $0.00474127、Cost_orig $0.0853428、GRADE A）← GPT-6 Luna max AA-public published-price
- Claude Sonnet 5 Adaptive Reasoning, Xhigh Effort AA-public published-price（Score 34.3842、Cost_adj $2.87204、Cost_orig $2.87204、GRADE A）← GPT-6 Luna max AA-public published-price
- DeepSeek V4 Flash 0731 Reasoning, Max Effort AA-public published-price（Score 34.3305、Cost_adj $0.219645、Cost_orig $0.219645、GRADE A）← GPT-6 Luna max AA-public published-price
- GLM-5.3 low AA-public published-price（Score 34.299、Cost_adj $0.852217、Cost_orig $0.852217、GRADE A）← GPT-6 Luna max AA-public published-price
- GPT-5.6 Terra high AA-public published-price（Score 34.2377、Cost_adj $0.0187707、Cost_orig $0.337873、GRADE A）← GPT-6 Luna max AA-public published-price
- Gemini 3.6 Flash high AA-public published-price（Score 33.9786、Cost_adj $0.928845、Cost_orig $0.928845、GRADE A）← GPT-6 Luna max AA-public published-price
- GPT-6 Sol low AA-public published-price（Score 33.9009、Cost_adj $0.00734671、Cost_orig $0.132241、GRADE A）← GPT-6 Luna max AA-public published-price
- GPT-5.5 medium AA-public published-price（Score 33.8044、Cost_adj $0.0500922、Cost_orig $0.901659、GRADE A）← GPT-6 Luna xhigh AA-public published-price
- Muse Spark 1.1 xhigh AA-public published-price（Score 33.7298、Cost_adj $1.38025、Cost_orig $1.38025、GRADE A）← GPT-6 Luna xhigh AA-public published-price
- GLM-5.2 max AA-public published-price（Score 33.7055、Cost_adj $0.964881、Cost_orig $0.964881、GRADE A）← GPT-6 Luna xhigh AA-public published-price
- Qwen3.8 27B xhigh AA-public published-price（Score 33.6963、Cost_adj $1.00731、Cost_orig $1.00731、GRADE A）← GPT-6 Luna xhigh AA-public published-price
- GPT-5.6 Sol low AA-public published-price（Score 33.4731、Cost_adj $0.0144801、Cost_orig $0.260642、GRADE A）← GPT-6 Luna xhigh AA-public published-price
- Gemini 3.5 Flash high AA-public published-price（Score 32.5983、Cost_adj $1.56254、Cost_orig $1.56254、GRADE A）← GPT-6 Luna xhigh AA-public published-price
- GPT-5.6 Luna high AA-public published-price（Score 32.1196、Cost_adj $0.00244342、Cost_orig $0.0439816、GRADE A）← GPT-6 Luna high AA-public published-price
- Claude Sonnet 5 Adaptive Reasoning, High Effort AA-public published-price（Score 31.6623、Cost_adj $1.79247、Cost_orig $1.79247、GRADE A）← GPT-6 Luna high AA-public published-price
- DeepSeek V4 Pro 0424 Reasoning, Max Effort AA-public published-price（Score 30.4497、Cost_adj $0.121521、Cost_orig $0.121521、GRADE A）← GPT-6 Luna high AA-public published-price
- GPT-5.6 Terra medium AA-public published-price（Score 30.0938、Cost_adj $0.0101874、Cost_orig $0.183373、GRADE A）← GPT-6 Luna high AA-public published-price
- Claude Sonnet 4.6 Adaptive Reasoning, Max Effort AA-public published-price（Score 30.0576、Cost_adj $2.48587、Cost_orig $2.48587、GRADE A）← GPT-6 Luna high AA-public published-price
- Gemini 3.1 Pro Preview unspecified AA-public published-price（Score 29.7186、Cost_adj $0.674732、Cost_orig $0.674732、GRADE A）← GPT-6 Luna high AA-public published-price
- Qwen3.7 Max unspecified AA-public published-price（Score 29.4572、Cost_adj $1.1473、Cost_orig $1.1473、GRADE A）← GPT-6 Luna medium AA-public published-price
- MiniMax-M3 unspecified AA-public published-price（Score 29.2203、Cost_adj $0.507613、Cost_orig $0.507613、GRADE A）← GPT-6 Luna medium AA-public published-price
- GPT-6 Sol Non-reasoning AA-public published-price（Score 28.0922、Cost_adj $0.0184136、Cost_orig $0.331445、GRADE A）← GPT-6 Luna medium AA-public published-price
- Claude Sonnet 5 Adaptive Reasoning, Medium Effort AA-public published-price（Score 28.0531、Cost_adj $0.999106、Cost_orig $0.999106、GRADE A）← GPT-6 Luna medium AA-public published-price
- Qwen3.8 27B medium AA-public published-price（Score 27.5508、Cost_adj $1.13306、Cost_orig $1.13306、GRADE A）← GPT-6 Luna medium AA-public published-price
- GPT-5.6 Terra low AA-public published-price（Score 27.4962、Cost_adj $0.00802565、Cost_orig $0.144462、GRADE A）← GPT-6 Luna medium AA-public published-price
- Kimi K2.6 unspecified AA-public published-price（Score 26.9792、Cost_adj $0.79977、Cost_orig $0.79977、GRADE A）← GPT-6 Luna medium AA-public published-price
- Quasar 438B max, based on GLM-5.2 AA-public published-price（Score 26.7373、Cost_adj $2.02461、Cost_orig $2.02461、GRADE A）← GPT-6 Luna medium AA-public published-price
- Apodex 1.1 unspecified AA-public published-price（Score 26.4104、Cost_adj $0.463725、Cost_orig $0.463725、GRADE A）← GPT-6 Luna medium AA-public published-price
- Qwen3.8 27B low AA-public published-price（Score 26.2048、Cost_adj $1.04822、Cost_orig $1.04822、GRADE A）← GPT-6 Luna medium AA-public published-price
- GLM-5.1 Reasoning AA-public published-price（Score 26.0586、Cost_adj $1.01926、Cost_orig $1.01926、GRADE A）← GPT-6 Luna medium AA-public published-price
- GPT-5.5 Instant June 2026 AA-public published-price（Score 26.0135、Cost_adj $0.0384159、Cost_orig $0.691485、GRADE A）← GPT-6 Luna medium AA-public published-price
- MiMo-V2.5-Pro unspecified AA-public published-price（Score 25.9869、Cost_adj $0.0540727、Cost_orig $0.0540727、GRADE A）← GPT-6 Luna medium AA-public published-price
- Kimi K2.7 Code unspecified AA-public published-price（Score 25.8121、Cost_adj $0.54119、Cost_orig $0.54119、GRADE A）← GPT-6 Luna medium AA-public published-price
- Hy3 unspecified AA-public published-price（Score 25.2973、Cost_adj $0.0743098、Cost_orig $0.0743098、GRADE A）← GPT-6 Luna medium AA-public published-price
- Qwen3.7 Plus unspecified AA-public published-price（Score 25.1622、Cost_adj $0.295171、Cost_orig $0.295171、GRADE A）← GPT-6 Luna medium AA-public published-price
- Inkling xhigh AA-public published-price（Score 24.9848、Cost_adj $0.607045、Cost_orig $0.607045、GRADE A）← GPT-5.6 Luna medium AA-public published-price
- Grok 4.3 high AA-public published-price（Score 24.8801、Cost_adj $0.0103312、Cost_orig $0.1653、GRADE A）← GPT-5.6 Luna medium AA-public published-price
- DeepSeek V4.1 Flash Non-Reasoning AA-public published-price（Score 24.6734、Cost_adj $0.1467、Cost_orig $0.1467、GRADE A）← GPT-5.6 Luna medium AA-public published-price
- Claude Sonnet 5 Adaptive Reasoning, Low Effort AA-public published-price（Score 24.2638、Cost_adj $0.508755、Cost_orig $0.508755、GRADE A）← GPT-5.6 Luna medium AA-public published-price
- DeepSeek V4 Flash 0420 Reasoning, Max Effort AA-public published-price（Score 24.1673、Cost_adj $0.117944、Cost_orig $0.117944、GRADE A）← GPT-5.6 Luna medium AA-public published-price
- GPT-5.4 mini xhigh AA-public published-price（Score 24.0682、Cost_adj $0.0227612、Cost_orig $0.409701、GRADE A）← GPT-5.6 Luna medium AA-public published-price
- Nemotron 3 Ultra 550B A55B Reasoning AA-public published-price（Score 22.9279、Cost_adj $0.54945、Cost_orig $0.54945、GRADE A）← GPT-5.6 Luna medium AA-public published-price
- MiniMax-M2.7 unspecified AA-public published-price（Score 22.7578、Cost_adj $0.101667、Cost_orig $0.101667、GRADE A）← GPT-5.6 Luna medium AA-public published-price
- Gemini 3.5 Flash-Lite unspecified AA-public published-price（Score 22.1685、Cost_adj $0.123527、Cost_orig $0.123527、GRADE A）← GPT-5.6 Luna medium AA-public published-price
- Qwen3.6 27B Reasoning AA-public published-price（Score 21.428、Cost_adj $0.621237、Cost_orig $0.621237、GRADE A）← GPT-5.6 Luna medium AA-public published-price
- GPT-5.6 Terra Non-reasoning AA-public published-price（Score 20.7797、Cost_adj $0.00776244、Cost_orig $0.139724、GRADE A）← GPT-6 Luna low AA-public published-price
- GPT-5.4 nano xhigh AA-public published-price（Score 20.7197、Cost_adj $0.0101711、Cost_orig $0.18308、GRADE A）← GPT-6 Luna low AA-public published-price
- Claude 4.5 Sonnet Reasoning AA-public published-price（Score 20.6662、Cost_adj $0.556581、Cost_orig $0.556581、GRADE A）← GPT-6 Luna low AA-public published-price
- Qwen3.8 27B Non-reasoning AA-public published-price（Score 20.1502、Cost_adj $2.48776、Cost_orig $2.48776、GRADE A）← GPT-6 Luna low AA-public published-price
- LongCat 2.0 unspecified AA-public published-price（Score 19.1123、Cost_adj $0.0589899、Cost_orig $0.0589899、GRADE A）← GPT-6 Luna low AA-public published-price
- Qwen3.5 397B A17B Reasoning AA-public published-price（Score 18.4204、Cost_adj $0.474577、Cost_orig $0.474577、GRADE A）← GPT-6 Luna low AA-public published-price
- GPT-6 Luna Non-reasoning AA-public published-price（Score 18.2617、Cost_adj $0.000618028、Cost_orig $0.0111245、GRADE A）← GPT-6 Luna low AA-public published-price
- Qwen3.6 35B A3B Reasoning AA-public published-price（Score 18.229、Cost_adj $0.475053、Cost_orig $0.475053、GRADE A）← GPT-6 Luna low AA-public published-price
- Muse Glimmer high AA-public published-price（Score 17.4754、Cost_adj $0.0567063、Cost_orig $0.0567063、GRADE A）← GPT-6 Luna low AA-public published-price
- Claude 4.5 Haiku Reasoning AA-public published-price（Score 16.8822、Cost_adj $0.207712、Cost_orig $0.207712、GRADE A）← GPT-6 Luna low AA-public published-price
- GPT-5 mini high AA-public published-price（Score 16.7731、Cost_adj $0.0029722、Cost_orig $0.0534997、GRADE A）← GPT-6 Luna low AA-public published-price
- Ring-2.6-1T unspecified AA-public published-price（Score 16.6172、Cost_adj $0.287157、Cost_orig $0.287157、GRADE A）← GPT-6 Luna low AA-public published-price
- Gemini 2.5 Pro unspecified AA-public published-price（Score 16.0779、Cost_adj $0.231666、Cost_orig $0.231666、GRADE A）← GPT-6 Luna low AA-public published-price
- Qwen3.5 122B A10B Reasoning AA-public published-price（Score 15.5694、Cost_adj $0.324747、Cost_orig $0.324747、GRADE A）← GPT-6 Luna low AA-public published-price
- Gemini 3.1 Flash-Lite unspecified AA-public published-price（Score 15.5543、Cost_adj $0.0394067、Cost_orig $0.0394067、GRADE A）← GPT-6 Luna low AA-public published-price
- GPT-5.6 Luna Non-reasoning AA-public published-price（Score 15.527、Cost_adj $0.000560657、Cost_orig $0.0100918、GRADE A）← GPT-6 Luna low AA-public published-price
- Mistral Medium 3.5 unspecified AA-public published-price（Score 14.1889、Cost_adj $0.436973、Cost_orig $0.436973、GRADE A）← GPT-6 Luna low AA-public published-price
- Grok 4.3 Non-reasoning AA-public published-price（Score 13.9927、Cost_adj $0.00859014、Cost_orig $0.137442、GRADE A）← GPT-6 Luna low AA-public published-price
- Nemotron 3.5 Lightning unspecified AA-public published-price（Score 12.8572、Cost_adj $0.0983157、Cost_orig $0.0983157、GRADE A）← GPT-6 Luna low AA-public published-price
- Nemotron 3 Super 120B A12B Reasoning AA-public published-price（Score 12.8288、Cost_adj $1.63907、Cost_orig $1.63907、GRADE A）← GPT-6 Luna low AA-public published-price
- Qwen3 235B A22B 2507 Reasoning AA-public published-price（Score 12.7109、Cost_adj $0.0805554、Cost_orig $0.0805554、GRADE A）← GPT-6 Luna low AA-public published-price
- Mercury 2.5 unspecified AA-public published-price（Score 12.3408、Cost_adj $0.0641727、Cost_orig $0.0641727、GRADE A）← GPT-6 Luna low AA-public published-price
- gpt-oss-120b high AA-public published-price（Score 11.6028、Cost_adj $0.107425、Cost_orig $0.107425、GRADE A）← GPT-6 Luna low AA-public published-price
- DeepSeek R1 Jan &#x27;25 AA-public published-price（Score 11.411、Cost_adj $0.261721、Cost_orig $0.261721、GRADE A）← GPT-6 Luna low AA-public published-price
- Mistral Small 4 Reasoning AA-public published-price（Score 11.2676、Cost_adj $0.0150468、Cost_orig $0.0150468、GRADE A）← GPT-6 Luna low AA-public published-price
- Granite 4.2 8B unspecified AA-public published-price（Score 11.0813、Cost_adj $0.0235961、Cost_orig $0.0235961、GRADE A）← GPT-6 Luna low AA-public published-price
- Qwen3 30B A3B 2507 Reasoning AA-public published-price（Score 9.80538、Cost_adj $0.0765561、Cost_orig $0.0765561、GRADE A）← GPT-6 Luna low AA-public published-price
- DeepSeek V3 0324 unspecified AA-public published-price（Score 9.72001、Cost_adj $0.105274、Cost_orig $0.105274、GRADE A）← GPT-6 Luna low AA-public published-price
- Mistral Large 3 unspecified AA-public published-price（Score 9.26609、Cost_adj $0.0538043、Cost_orig $0.0538043、GRADE A）← GPT-6 Luna low AA-public published-price
- Qwen3 Coder Next unspecified AA-public published-price（Score 9.23682、Cost_adj $0.551804、Cost_orig $0.551804、GRADE A）← GPT-6 Luna low AA-public published-price
- Granite 4.2 3B unspecified AA-public published-price（Score 9.05588、Cost_adj $0.00598025、Cost_orig $0.00598025、GRADE A）← GPT-6 Luna low AA-public published-price
- gpt-oss-20b high AA-public published-price（Score 8.96752、Cost_adj $0.0124606、Cost_orig $0.0124606、GRADE A）← GPT-6 Luna low AA-public published-price
- NVIDIA Nemotron 3 Nano 30B A3B Reasoning AA-public published-price（Score 8.89614、Cost_adj $0.0167516、Cost_orig $0.0167516、GRADE A）← GPT-6 Luna low AA-public published-price
- DeepSeek V3 Dec &#x27;24 AA-public published-price（Score 8.48687、Cost_adj $0.0197518、Cost_orig $0.0197518、GRADE A）← GPT-6 Luna low AA-public published-price
- Solar Pro 3 unspecified AA-public published-price（Score 7.81552、Cost_adj $0.0794271、Cost_orig $0.0794271、GRADE A）← GPT-6 Luna low AA-public published-price
- Mistral Small 3.1 unspecified AA-public published-price（Score 7.11736、Cost_adj $0.0350286、Cost_orig $0.0350286、GRADE A）← GPT-6 Luna low AA-public published-price
- Celeris-1 unspecified AA-public published-price（Score 6.34695、Cost_adj $0.0501576、Cost_orig $0.0501576、GRADE A）← GPT-6 Luna low AA-public published-price
- Ministral 3 14B unspecified AA-public published-price（Score 6.04437、Cost_adj $0.0194364、Cost_orig $0.0194364、GRADE A）← GPT-6 Luna low AA-public published-price
- Ministral 3 8B unspecified AA-public published-price（Score 5.47767、Cost_adj $0.0110864、Cost_orig $0.0110864、GRADE A）← GPT-6 Luna low AA-public published-price
- Ministral 3 3B unspecified AA-public published-price（Score 4.8376、Cost_adj $0.00784686、Cost_orig $0.00784686、GRADE A）← GPT-6 Luna low AA-public published-price

詳細全精度數據與每行 notes／URL 見 result.json。來源研究限制見原 run-notes.md；本試驗沒有擷取新資料，亦不取代正式三 picks。
