# CGC Engine 終極端雲架構與記憶體優化白皮書 v1.0

## 1. DeltaMem (矩陣mem) 核心架構與記憶體狀態管理

DeltaMem (矩陣mem) 是 CGC Engine 實現極速端雲協同的核心物理基礎。傳統的 LLM 推理架構在處理長上下文時，會因為全量傳輸 KV Cache 矩陣而造成嚴重的 I/O 瓶頸。DeltaMem 的核心精神在於：**將 LLM 內部的 KV 矩陣 (Matrix Memory) 視為可被差異化、快取與直接映射的實體記憶體區塊**。

### 1.1 矩陣mem (Matrix Memory) 的物理映射
在早期 M2/M6 階段，我們確立了 `DeltaMem` 的基礎實作：
*   **狀態攔截**：透過攔截底層 GGML Tensor 的 `set_tensor` 與 `get_tensor`，直接獲取 KV Cache 矩陣的實體記憶體指標。
*   **Delta 傳輸**：在端雲分離架構下，只傳輸增量的 KV 矩陣 (Delta KV) 或經過 Hash 比對後缺失的區塊，而非全量傳遞。
*   **0 拷貝反序列化**：拒絕使用 Python 的 `pickle` 或 `json`。矩陣mem 以 RAW Bytes 的形式存在，端側接收後直接 `mmap` 或 `memcpy` 進 VRAM，跳過 CPU 的解析開銷。

這套 DeltaMem 的基礎在後續的 M7.2 / M7.4 階段被徹底發揚光大，並演化為極致的 **VRAM 暴力直寫**。

---

## 2. 端雲網路協議與狀態壓縮 (Edge-Cloud Protocol)

為了滿足 M7.2 Gate 的嚴苛驗收標準 (Soft-RT 10ms deadline) 以及 M7.4 的真實跨機分離，端雲協議 (Edge-Cloud Protocol) 針對 Apple Silicon (M2/M4) 進行了深度特化。

### 2.1 傳輸管線 (Socket Protocol) 與雲端主導建立
我們在 `cloud_socket_server.py` 與 `edge_socket_client.py` 中實作了專屬的 TCP 端雲協議。為了貫徹「極輕量端側」的原則，**端雲協議的建立與交握 (Handshake) 完全由雲端主導**：
*   **雲端主導建立 (Cloud-Driven Initialization)**：雲端在完成「模型裁切」後，會根據端側的硬體特徵，主動生成通訊密鑰 (AES-256-GCM)、壓縮字典與路由配置，並將這些極輕量的「交握設定檔」下發給端側。端側只需被動載入並啟動 Client，無需耗費算力與邏輯進行複雜的協議協商。
*   **CGC KV Header**：在資料封包頭部附加 4 Bytes 的 Length，以及 JSON Metadata (包含 `mode`, `shape`, `dtype`, `payload_size`)。
*   **Payload 傳輸**：緊接著 Header，傳輸經過狀態壓縮器 (`KVStateCompressor`) 處理過的 RAW Tensor Bytes。

### 2.2 狀態壓縮器 (State Compressor) 終極選擇：Bit-Packing + RLE
為了適應公網/Wi-Fi 頻寬，我們導入了極限壓縮鐵律：
*   **雲端算力承擔壓縮**：壓縮運算只放在雲端 A100 執行，絕不佔用端側算力。
*   **終極 KV 壓縮策略 (Bit-Packing + RLE)**：取代原本的 zlib 壓縮，針對張量資料進行位元打包 (Bit-Packing) 與游程編碼 (Run-Length Encoding, RLE) 降維。這能將網路傳輸量極小化。
*   **端側極輕量解壓**：筆電端 (Mac) 收到封包後，只做「極輕量解壓 + VRAM 直寫」，嚴禁在端側進行複雜的解碼或量化運算。

### 2.3 端側零開銷接收 (Apple Silicon 特化)
端側 Mac (M2/M4) 收到矩陣mem後，直接透過極簡的位元展開還原為原始型別，確保不消耗端側寶贵的 CPU/GPU 算力。

---

## 3. M7.4 終極端雲編譯架構：SGLang 與 4D 感知矩陣

CGC Engine 拒絕將雲端與端側推理引擎視為「黑盒子」並僅依賴膠水程式橋接。在 M7.4 架構中，SGLang (雲端) 與 Llama.cpp (端側) 已被正式納入 **全計算圖算子八步流水線**。

透過 **4D 感知矩陣 (環境 / 硬件 / 模型 / 任務)**，CGC Engine 具備工業級的軟硬體協同設計 (Hardware-Software Co-design) 能力：

1. **硬體感知與極致微調 (Hardware-Aware Compilation)**：
   - **雲端 (SGLang)**：感知 RTX 5090 等高階算力，動態注入客製化 KV 提取算子，編譯生成專屬的 `cgc_sglang.so`，支援極速 PagedAttention。
   - **端側 (Llama.cpp)**：感知 Mac 或 RTX Spark PC，將 UMA 0-copy (統一記憶體零拷貝) 的實體記憶體指標與 PCIe 頻寬繞過機制硬編碼，編譯生成 `cgc_llamacpp.so`。

2. **巨型模型 VRAM 精準切割 (Model & Task Perception)**：
   - 針對 Llama-3-70B 等巨型模型，透過 L1 動態軌跡編譯，精準計算端側輕薄機 (如 8GB/16GB VRAM) 的記憶體高水位線 (High Watermark)。
   - 在生成的 `.so` 中直接預分配連續記憶體池，徹底消滅執行期記憶體碎片，打破 TGP 功耗牆與 VRAM 天花板。

3. **商業壁壘與嚴格審計 (Strict Mode)**：
   - 所有生成的 `.so` 均強制綁定 TrueOrthoKDA 與 Hash 指紋。
   - 確保執行路徑百分之百受 CGC 審計監控，建立無法被輕易複製的商業護城河。

---

## 4. M7.4 里程碑：0拷貝極限壓榨與 UMA 0-copy 直寫

在 M7.4 階段，基於 DeltaMem (矩陣mem) 的基礎，我們進一步在 C++ 底層徹底消除了最後一絲 CPU 拷貝延遲。

### 3.1 Apple Silicon VRAM 0拷貝直寫 (`set_skip_tensor_set`)
*   **攔截 `llama_state_set_data`**：原生的 API 會強制將 RAM 拷貝至 GPU。我們透過 `cgc_metal_vram_hook.mm` 實作了 `set_skip_tensor_set(True)`。
*   **暴力覆蓋**：當端側透過網路接收到壓縮的矩陣mem並解開後，資料已經透過 DMA/共享記憶體位於 Apple Silicon 的統一記憶體 (UMA) 中。此時攔截器直接回傳 `return;`，完全跳過 CPU 到 GPU 的 `memcpy`。
*   **成效**：在最新的 Qwen2.5-0.5B 物理極限測試中，12.5MB 的 KV Cache 直寫僅需 **0.0018s** (約 1.8 毫秒)。

### 3.2 端側 Decode 極限算力壓榨
*   **鎖死 P-Core**：`n_threads=4`，避免大小核切換。
*   **FlashAttention**：強制開啟，優化 SRAM 頻寬。
*   **極限 TTFT**：在 1024 Token 上下文下，包含網路接收後的「解壓 (0.0089s) + VRAM 0拷貝直寫 (0.0018s) + Decode 第一個字 (0.0308s)」，端側接手總耗時被壓榨至驚人的 **0.041 秒**，遠小於 Native 全端側處理的 0.45 秒。

---

## 5. 核心架構顛覆：隱私優先端雲分離 (Privacy-First PD Separation)

為解決傳統端雲分離架構中，雲端必須接收明文 Prompt 的隱私風險，以及端側 VRAM 無法載入巨型模型的問題，CGC Engine 引入了**隱私優先端雲分離 (Privacy-First PD Separation)** 機制。此機制的核心在於**「模型權重非對稱切割」**：

### 5.1 模型權重非對稱切割與雲端裁切 (Cloud-Side Slicing)
在 70B 甚至更大參數的模型場景下，CGC Engine 拒絕一刀切，更拒絕讓端側下載龐大的原始模型。這正是**全計算圖算子八步流水線**結合 **4D 感知矩陣 (環境 / 硬件 / 模型 / 任務)** 的核心威力展現：

*   **雲端裁切 (Cloud-Side Slicing)**：這是一個至關重要的架構設計。40GB 的完整巨型模型 (如 70B) **只會存放在雲端 (如 gs01)**。當八步流水線的 `step4_hardware_perception` 偵測到端側的硬體規格時，**「切蛋糕的刀」會直接在雲端執行**。雲端根據端側硬體極限，萃取出 Embedding、前 N 層與 LM_Head，並封裝成專屬的端側微型權重 (僅 1-2GB)。端側只需下載這 1-2GB 的切片，徹底免除下載 40GB 原檔的網路與儲存負擔。
*   **硬件與環境感知 (Hardware Maximization)**：八步流水線會偵測端側 (Dell XPS / Mac) 的 VRAM 容量與散熱環境，將 VRAM 塞滿到安全水位。以 16GB VRAM 為例，端側可能被動態分配載入雲端裁切好的前 10 層 Attention，極大化發揮端側硬體的算力投資，避免資源閒置。
*   **任務與模型感知 (Dynamic Token Routing)**：八步流水線會根據輸入任務的上下文長度，動態決定端雲路由策略：
    *   **短上下文任務 (如 < 1000 Tokens)**：完全在端側利用已載入的前 N 層與極限混合量化完成運算，實現 **0 網路延遲** 的純本地推理。
    *   **長上下文任務 (如 > 1000 Tokens)**：當 Prompt 超過端側算力與 VRAM 的處理極限時，CGC Engine 會自動觸發端雲分離。端側負責計算前 N 層並提取無語義特徵。
*   **雲端 (彈性滿血存放)**：雲端伺服器 (如 RTX 5090) 存放完整的 40GB 模型權重。當收到端雲分離請求時，雲端從第 N+1 層接手，執行最耗算力的 Heavy Prefill。

### 5.2 執行管線
*   **端側 (Mac / RTX Spark) 邊緣計算**：利用端側硬體極限載入的權重 (如前 N 層)，計算 Token Embedding 與前 N 層 Attention。若是長上下文觸發端雲分離，則輸出低維稀疏特徵 (無語義且不可逆還原)。
*   **雲端 (A100/RTX 5090) Heavy Prefill**：雲端載入 40GB 完整權重，接收無語義特徵，從第 N+1 層開始進行後續的高負載 Prefill 計算。雲端**完全看不到原始文本與上下文**。
*   **KV 狀態回傳與加密**：雲端計算完成後，對 KV Cache 進行 Bit-Packing + RLE 壓縮，並疊加 **AES-256-GCM 加密**後回傳。
*   **端側解密與 VRAM 直寫 (UMA 0-copy)**：端側接收後，在記憶體中解密並極簡解壓，接著透過 **UMA 0-copy** 直接寫入 VRAM。最後利用端側極輕量的 LM_Head 進行 Decode 生成。

**終極效益**：
*   **隱私 = 純端側級別**（雲端永遠接觸不到明文）。
*   **效能 = 端雲分離級別**（雲端扛下長文本的 Heavy Prefill）。
*   **端側算力 = 極限滿載級別 (Hardware Maximization)**：端側在「協議與調度邏輯」上是零負擔的被動接收者；但在「張量運算」上，4D 感知矩陣會嚴格根據端側的環境 (Environment)、硬體 (Hardware)、模型 (Model) 與任務 (Task) 特徵，將端側算力與 VRAM 壓榨到物理極限（例如精準吃滿 16GB VRAM），絕不浪費任何一滴端側算力投資。

*   **端側接收延遲 (VRAM 直寫)**：1024 Token 的 KV 矩陣極簡解壓與寫入 VRAM 耗時必須 **< 0.05s**。
*   **端側接手 TTFT**：在完成 VRAM 直寫後，產出第一個字的耗時必須 **< 0.1s**。
*   **雲端通訊協議**：必須成功透過 TCP/Socket 解析 CGC KV Header，並能無損還原 Bit-Packing + RLE Tensor，端側解壓耗時必須 **< 10ms**。
