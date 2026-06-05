#!/usr/bin/env python3
"""
CGC Engine CLI - Unified Pipeline Interface

Commands:
    cgc pipeline    - Run unified 8-step pipeline (LLM/MLX)
    cgc info        - Display system information

Architecture:
    CLI -> LLMAutoPipeline -> (LLM1 -> SkVM -> FX -> KDA -> AOTInductor) -> Backend

    Backends (Execution Engine):
        vllm        - vLLM (CUDA) inference
        llama.cpp   - llama.cpp GGUF inference
        mlx         - Apple Silicon MLX inference

    Execution Modes:
        native      - Original runtime baseline
        inject      - Inject custom backend into runtime
        compile     - Full-graph analyze + compile (.so)
"""

import argparse
import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

def add_pipeline_subparser(subparsers):
    parser = subparsers.add_parser(
        'pipeline',
        help='Run unified 8-step pipeline (LLM/MLX)',
        description='Run the unified 8-step pipeline for vllm, llama.cpp, or mlx backends',
    )
    parser.add_argument(
        '--mode',
        type=str,
        default='llm',
        choices=['llm', 'mlx-step67', 'edge-cloud'],
        help='Pipeline mode',
    )
    parser.add_argument(
        '--backend',
        type=str,
        default='auto',
        choices=['auto', 'mlx', 'mlx-lm', 'mlx_lm', 'vllm', 'llama.cpp', 'llama_cpp', 'mindspeed', 'mindspeed-llm', 'megatrain', 'mlx-tune'],
        help='Target backend',
    )
    parser.add_argument(
        '--model',
        type=str,
        default='Qwen/Qwen2.5-7B-Instruct',
        help='Model id for mlx/vllm backend',
    )
    parser.add_argument(
        '--gguf-path',
        type=str,
        default=None,
        help='GGUF path or HF spec for llama.cpp backend',
    )
    parser.add_argument(
        '--ppl-wikitext2',
        action='store_true',
        default=False,
        help='Use WikiText2 (wiki.test.raw) for llama.cpp perplexity gate',
    )
    parser.add_argument(
        '--ppl-file',
        type=str,
        default='',
        help='Perplexity corpus file path (overrides WikiText2 auto-resolve/download)',
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='',
        help='Output directory for pipeline artifacts (default: <repo>/Output/PipelineRuns/<backend>/<model>/<run_id>)',
    )
    parser.add_argument(
        '--require-cuda',
        action='store_true',
        default=False,
        help='Fail-close: require CUDA-only runtime (sets CGC_REQUIRE_CUDA=1)',
    )
    parser.add_argument(
        '--require-mlx',
        action='store_true',
        default=False,
        help='Fail-close: require MLX/MPS runtime (sets CGC_REQUIRE_MLX=1)',
    )
    parser.add_argument(
        '--fingerprint-lock',
        type=str,
        default='',
        help='Fail-close: backend fingerprint lock json path (sets CGC_BACKEND_FINGERPRINT_LOCK=...)',
    )
    parser.add_argument(
        '--contexts',
        type=str,
        default='128,512,1024,2048,4096,8192',
        help='Comma-separated context lengths',
    )
    parser.add_argument(
        '--milestone',
        type=str,
        default='auto',
        choices=['auto', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm71', 'm72', 'm73'],
        help='Target milestone (controls gate strictness and recommended defaults)',
    )
    parser.add_argument(
        '--milestone-seq',
        type=str,
        default='',
        help='Run multiple milestones sequentially, e.g. m3,m4,m5,m6,m7',
    )
    parser.add_argument(
        '--seq-output-dir-template',
        type=str,
        default='',
        help='When --milestone-seq is set: template for per-milestone output_dir (supports {milestone}). If not set, uses --output-dir; if no {milestone}, appends /<milestone>.',
    )
    parser.add_argument(
        '--seq-stop-on-fail',
        action='store_true',
        default=False,
        help='When --milestone-seq is set: stop after first FAIL (default: continue to produce PASS/FAIL reports for all milestones).',
    )
    parser.add_argument(
        '--m4-speedup-min',
        type=float,
        default=1.5,
        help='M4 performance gate minimum speedup ratio (baseline/optimized)',
    )
    parser.add_argument(
        '--m4-require-autopd',
        action='store_true',
        default=False,
        help='M4 only: require Auto-PD product gate (expects CGC_M4_AUTOPD_MANIFEST to be provided and PASS)',
    )
    parser.add_argument(
        '--m4-autopd-manifest',
        type=str,
        default='',
        help='M4 only: Auto-PD manifest json path for product gate (used when --m4-require-autopd)',
    )
    parser.add_argument(
        '--m4-require-omlx-flashmoe',
        action='store_true',
        default=False,
        help='M4 only: require OMLX+FlashMoE on-demand download gate',
    )
    parser.add_argument(
        '--m4-omlx-flashmoe-manifest',
        type=str,
        default='',
        help='M4 only: OMLX+FlashMoE manifest json path',
    )
    parser.add_argument(
        '--exec-mode',
        type=str,
        default='native',
        choices=['native', 'inject', 'compile'],
        help='Execution mode: native=original runtime; inject=inject custom backend into runtime; compile=full-graph analyze+compile and run in compiled engine',
    )
    parser.add_argument(
        '--inject-mode',
        type=str,
        default='attention',
        choices=['forward', 'back', 'attention', 'compute'],
        help='When --exec-mode=inject: forward=full-graph forward hijack; back=backward hijack; attention=swap attention backend; compute=hijack full compute via full-graph compile (no attention backend).',
    )
    parser.add_argument(
        '--edge-cloud-base-url',
        type=str,
        default='',
        help='Edge-cloud mode only: cloud OpenAI-compatible base url (no trailing /v1). Empty means skip cloud prefill.',
    )
    parser.add_argument(
        '--edge-cloud-model',
        type=str,
        default='',
        help='Edge-cloud mode only: cloud model id (empty means reuse --model).',
    )
    parser.add_argument(
        '--edge-cloud-api-key',
        type=str,
        default=None,
        help='Edge-cloud mode only: cloud api key (optional). If omitted, uses env EDGE_CLOUD_API_KEY.',
    )
    parser.add_argument(
        '--edge-cloud-timeout-s',
        type=int,
        default=120,
        help='Edge-cloud mode only: cloud request timeout seconds.',
    )
    parser.add_argument(
        '--mindspeed-base-url',
        type=str,
        default='',
        help='MindSpeed backend only: OpenAI-compatible base url (no trailing /v1).',
    )
    parser.add_argument(
        '--mindspeed-model',
        type=str,
        default='',
        help='MindSpeed backend only: model id (empty means reuse --model).',
    )
    parser.add_argument(
        '--mindspeed-api-key',
        type=str,
        default=None,
        help='MindSpeed backend only: api key (optional). If omitted, uses env MINDSPEED_API_KEY.',
    )
    parser.add_argument(
        '--mindspeed-timeout-s',
        type=int,
        default=120,
        help='MindSpeed backend only: request timeout seconds.',
    )
    parser.add_argument(
        '--mindspeed-exec-driver',
        type=str,
        default='http',
        choices=['http', 'subprocess'],
        help='MindSpeed backend only: http=call OpenAI endpoint; subprocess=run MindSpeed-LLM script locally and measure elapsed time.',
    )
    parser.add_argument(
        '--mindspeed-subprocess-cmd',
        type=str,
        default='',
        help='MindSpeed backend only: command template for subprocess driver. Supports {context},{gen_tokens},{model},{mcore_dir},{source_hf},{precision},{prompt}.',
    )
    parser.add_argument(
        '--mindspeed-subprocess-cwd',
        type=str,
        default='',
        help='MindSpeed backend only: working directory for subprocess command.',
    )
    parser.add_argument(
        '--mindspeed-subprocess-env-source',
        type=str,
        default='',
        help='MindSpeed backend only: shell script to source before running subprocess cmd (bash -lc).',
    )
    parser.add_argument(
        '--mindspeed-source-hf',
        type=str,
        default='',
        help='MindSpeed backend only: HF model id/dir that the Mcore checkpoint was converted from (for config capture/report).',
    )
    parser.add_argument(
        '--mindspeed-mcore-dir',
        type=str,
        default='',
        help='MindSpeed backend only: Megatron-core (Mcore) checkpoint directory path (for validation/report).',
    )
    parser.add_argument(
        '--mindspeed-precision',
        type=str,
        default='fp8_mixed',
        help='MindSpeed backend only: weight precision hint for report (e.g., fp8_mixed, bf16).',
    )
    parser.add_argument(
        '--edge-prompt',
        type=str,
        default='hello',
        help='Edge-cloud mode only: prompt text for prefill / decode.',
    )
    parser.add_argument(
        '--edge-prefill-max-tokens',
        type=int,
        default=1,
        help='Edge-cloud mode only: max tokens for cloud prefill request (default 1).',
    )
    parser.add_argument(
        '--enable-mtp',
        action='store_true',
        default=False,
        help='Edge-cloud mode only: enable multi-token prediction decode plan flag.',
    )
    parser.add_argument(
        '--enable-cuda-graph',
        action='store_true',
        default=False,
        help='Edge-cloud mode only: enable CUDA Graph freeze plan flag (CUDA only).',
    )
    parser.add_argument(
        '--task-type',
        type=str,
        default='inference',
        choices=['inference', 'train', 'tune', 'multimodal'],
        help='Task type: inference (default), train (FSDP-Aware whole-layer compile), tune (LoRA Unified Memory), multimodal (dynamic shape + split unification)',
    )
    parser.add_argument(
        '--m5-require-ort',
        action='store_true',
        default=False,
        help='M5 only: require ONNX Runtime edge gate (expects onnxruntime installed + model path)',
    )
    parser.add_argument(
        '--m5-ort-model',
        type=str,
        default='',
        help='M5 only: ONNX model path for ORT edge gate',
    )
    parser.add_argument(
        '--m5-ort-ep',
        type=str,
        default='',
        help='M5 only: ORT execution provider for ORT edge gate (default CPUExecutionProvider)',
    )
    parser.add_argument(
        '--m5-ort-custom-ops-lib',
        type=str,
        default='',
        help='M5 only: custom ops shared library path for ORT edge gate (optional)',
    )
    parser.add_argument(
        '--gen-tokens',
        type=int,
        default=128,
        help='Decode tokens per run',
    )
    parser.add_argument(
        '--warmup-runs',
        type=int,
        default=1,
        help='Warmup runs per context',
    )
    parser.add_argument(
        '--runs',
        type=int,
        default=3,
        help='Runs per context',
    )
    parser.add_argument(
        '--enable-hooks',
        action='store_true',
        default=False,
        help='Enable hooks/opcode optimized path (mlx only)',
    )
    parser.add_argument(
        '--enable-ortho-kda',
        action='store_true',
        default=False,
        help='Enable OrthoKDA cache semantics',
    )
    parser.add_argument(
        '--ortho-kda-base-dim',
        type=int,
        default=64,
        help='OrthoKDA base dim',
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=0,
        help='Random seed',
    )
    parser.add_argument(
        '--input-shape',
        type=int,
        nargs=3,
        default=[2, 256, 1024],
        help='Input shape for mlx-step67: batch seq hidden',
    )
    parser.add_argument(
        '--enable-llm1',
        action='store_true',
        default=False,
        help='Enable LLM1 translation in step5 (vLLM OpenAI-compatible endpoint)',
    )
    parser.add_argument(
        '--llm1-base-url',
        type=str,
        default='http://127.0.0.1:8000',
        help='LLM1 endpoint base url, e.g. http://127.0.0.1:8000',
    )
    parser.add_argument(
        '--llm1-model',
        type=str,
        default='',
        help='LLM1 model name at endpoint (empty means reuse --model)',
    )
    parser.add_argument(
        '--llm1-api-key',
        type=str,
        default=None,
        help='LLM1 api key (optional). If omitted, uses env LLM1_API_KEY',
    )
    parser.add_argument(
        '--llm1-timeout-s',
        type=int,
        default=300,
        help='LLM1 request timeout seconds',
    )
    parser.add_argument(
        '--llm1-input-path',
        type=str,
        default=None,
        help='Path to backend kernel/operator code file for LLM1 translation',
    )
    parser.add_argument(
        '--enable-fullgraph-aot',
        action='store_true',
        default=False,
        help='Enable transformers safetensors full-graph AOTInductor compile + end-to-end benchmark',
    )
    parser.add_argument(
        '--fullgraph-model',
        type=str,
        default='',
        help='HF model id for fullgraph (empty means reuse --model)',
    )
    parser.add_argument(
        '--fullgraph-prompt',
        type=str,
        default='hello',
        help='Prompt text for fullgraph benchmark',
    )
    parser.add_argument(
        '--fullgraph-max-new-tokens',
        type=int,
        default=16,
        help='Decode tokens for fullgraph benchmark',
    )
    parser.add_argument(
        '--fullgraph-non-strict',
        action='store_true',
        default=False,
        help='Do not fail pipeline when fullgraph aot fails',
    )
    parser.add_argument(
        '--enable-skvm-verify',
        action='store_true',
        default=False,
        help='Enable SkVM verify in step3 (auto-enabled when --enable-llm1; uses --skvm-input or step5 LLM1 output)',
    )
    parser.add_argument(
        '--skvm-input',
        type=str,
        default=None,
        help='Path to pytorch graph/module file for skvm verify (optional if step5 LLM1 is enabled)',
    )
    parser.add_argument(
        '--skvm-cli',
        type=str,
        default='skvm',
        help='SkVM CLI executable',
    )
    parser.add_argument(
        '--skvm-auto-install',
        action='store_true',
        default=False,
        help='Auto-install official SkVM (skillvm.ai) when --skvm-cli=skvm is missing',
    )
    parser.add_argument(
        '--enable-skillvm-aot',
        action='store_true',
        default=False,
        help='Run official SkVM (skillvm.ai) profile+aot-compile to produce an AOT-compiled SKILL artifact (stored under Output).',
    )
    parser.add_argument(
        '--skillvm-target-model',
        type=str,
        default='',
        help='SkVM target model id (<provider>/<model-id>), e.g. openrouter/qwen/qwen3.5-35b-a3b',
    )
    parser.add_argument(
        '--skillvm-compiler-model',
        type=str,
        default='',
        help='SkVM compiler backend model id (<provider>/<model-id>), e.g. anthropic/claude-sonnet-4.6',
    )
    parser.add_argument(
        '--skillvm-adapter',
        type=str,
        default='bare-agent',
        help='SkVM adapter (default: bare-agent)',
    )
    parser.add_argument(
        '--skvm-dtype',
        type=str,
        default='fp16',
        help='SkVM dtype, e.g. fp16/bf16/fp32',
    )
    parser.add_argument(
        '--skvm-timeout-s',
        type=int,
        default=30,
        help='SkVM verify timeout seconds',
    )
    parser.add_argument(
        '--skvm-non-strict',
        action='store_true',
        default=False,
        help='Do not fail pipeline when skvm verify fails',
    )
    parser.add_argument(
        '--report-path',
        type=str,
        default='',
        help='Report JSON path (default: <output_dir>/report.json)',
    )
    parser.add_argument(
        '--bundle-export-dir',
        type=str,
        default='',
        help='Optional: export a self-contained artifact bundle directory for edge deployment (agent pipeline only).',
    )
    parser.add_argument(
        '--bundle-import-manifest',
        type=str,
        default='',
        help='Edge-cloud mode only: import artifact bundle from a manifest path or URL (http/https/file).',
    )
    parser.add_argument(
        '--bundle-import-dir',
        type=str,
        default='',
        help='Edge-cloud mode only: directory to store imported bundle payload (default: <output_dir>/bundle_cache).',
    )
    parser.add_argument(
        '--bundle-artifact-base-url',
        type=str,
        default='',
        help='Edge-cloud mode only: base URL to download bundle payload files (if manifest contains relative paths).',
    )
    parser.set_defaults(func=pipeline_command)

def pipeline_command(args):
    milestone_seq_raw = str(getattr(args, "milestone_seq", "") or "").strip()
    if milestone_seq_raw != "":
        import argparse as _argparse
        import re as _re

        def _clear_milestone_env() -> None:
            for k in list(os.environ.keys()):
                if _re.match(r"^CGC_M[0-9]", str(k)):
                    try:
                        del os.environ[k]
                    except Exception:
                        pass

        allowed = {"m2", "m3", "m4", "m5", "m6", "m7", "m71", "m72", "m73"}
        seq = [s.strip().lower() for s in milestone_seq_raw.split(",") if s.strip() != ""]
        for m in seq:
            if m not in allowed:
                print(json.dumps({"ok": False, "error": f"invalid --milestone-seq item: {m}"}, ensure_ascii=False))
                return 2
        base_vars = dict(vars(args))
        overall_ok = True
        last_rc = 0
        for m in seq:
            child = _argparse.Namespace(**base_vars)
            setattr(child, "milestone_seq", "")
            setattr(child, "milestone", str(m))

            out_tmpl = str(getattr(child, "seq_output_dir_template", "") or "").strip()
            if out_tmpl == "":
                out_tmpl = str(getattr(child, "output_dir", "") or "").strip()
            if out_tmpl != "":
                if "{milestone}" in out_tmpl:
                    setattr(child, "output_dir", out_tmpl.format(milestone=str(m)))
                else:
                    try:
                        setattr(child, "output_dir", str(Path(out_tmpl) / str(m)))
                    except Exception:
                        setattr(child, "output_dir", out_tmpl + "/" + str(m))

            rpt = str(getattr(child, "report_path", "") or "").strip()
            if rpt != "":
                if "{milestone}" in rpt:
                    setattr(child, "report_path", rpt.format(milestone=str(m)))
                else:
                    print(json.dumps({"ok": False, "error": "when --milestone-seq is set: --report-path must be empty or contain {milestone}"}, ensure_ascii=False))
                    return 2

            bdir = str(getattr(child, "bundle_export_dir", "") or "").strip()
            if bdir != "":
                if "{milestone}" in bdir:
                    setattr(child, "bundle_export_dir", bdir.format(milestone=str(m)))
                else:
                    print(json.dumps({"ok": False, "error": "when --milestone-seq is set: --bundle-export-dir must be empty or contain {milestone}"}, ensure_ascii=False))
                    return 2

            _clear_milestone_env()
            rc = pipeline_command(child)
            last_rc = int(rc)
            if int(rc) != 0:
                overall_ok = False
                if bool(getattr(args, "seq_stop_on_fail", False)):
                    break
        return 0 if overall_ok else int(last_rc or 1)

    if bool(args.enable_llm1) and not bool(args.enable_skvm_verify):
        args.enable_skvm_verify = True

    mode = str(args.mode)
    backend = str(args.backend)
    model = str(args.model)
    gguf_path = str(args.gguf_path) if args.gguf_path is not None else None
    exec_mode = str(getattr(args, "exec_mode", "native"))
    milestone = str(getattr(args, "milestone", "auto") or "auto").strip().lower()
    if bool(getattr(args, "m4_require_autopd", False)):
        os.environ["CGC_M4_REQUIRE_AUTOPD"] = "1"
    autopd_manifest = str(getattr(args, "m4_autopd_manifest", "") or "").strip()
    if autopd_manifest != "":
        os.environ["CGC_M4_AUTOPD_MANIFEST"] = autopd_manifest

    if bool(getattr(args, "m4_require_omlx_flashmoe", False)):
        os.environ["CGC_M4_REQUIRE_OMLX_FLASHMOE"] = "1"
    omlx_manifest = str(getattr(args, "m4_omlx_flashmoe_manifest", "") or "").strip()
    if omlx_manifest != "":
        os.environ["CGC_M4_OMLX_FLASHMOE_MANIFEST"] = omlx_manifest

    if bool(getattr(args, "m5_require_ort", False)):
        os.environ["CGC_M5_REQUIRE_ORT"] = "1"
    ort_model = str(getattr(args, "m5_ort_model", "") or "").strip()
    if ort_model != "":
        os.environ["CGC_M5_ORT_MODEL"] = ort_model
    ort_ep = str(getattr(args, "m5_ort_ep", "") or "").strip()
    if ort_ep != "":
        os.environ["CGC_M5_ORT_EP"] = ort_ep
    ort_custom_ops = str(getattr(args, "m5_ort_custom_ops_lib", "") or "").strip()
    if ort_custom_ops != "":
        os.environ["CGC_M5_ORT_CUSTOM_OPS_LIB"] = ort_custom_ops

    def _pick_default_gguf() -> Optional[str]:
        try:
            base = Path(project_root).resolve() / "Output" / "Models"
            cands = list(base.rglob("*.gguf"))
            if not cands:
                return None
            cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return str(cands[0])
        except Exception:
            return None

    if milestone in {"m2", "m3", "m4", "m5", "m6", "m7", "m73"}:
        os.environ["CGC_MILESTONE"] = milestone

    require_cuda_flag = bool(getattr(args, "require_cuda", False))
    require_mlx_flag = bool(getattr(args, "require_mlx", False))
    if require_cuda_flag and require_mlx_flag:
        print(json.dumps({"ok": False, "error": "invalid args: both --require-cuda and --require-mlx are set"}, ensure_ascii=False))
        return 2
    if require_cuda_flag:
        os.environ["CGC_REQUIRE_CUDA"] = "1"
    if require_mlx_flag:
        os.environ["CGC_REQUIRE_MLX"] = "1"
    fingerprint_lock = str(getattr(args, "fingerprint_lock", "") or "").strip()
    if fingerprint_lock != "":
        if not Path(fingerprint_lock).expanduser().exists():
            print(json.dumps({"ok": False, "error": f"fingerprint lock not found: {fingerprint_lock}"}, ensure_ascii=False))
            return 2
        os.environ["CGC_BACKEND_FINGERPRINT_LOCK"] = fingerprint_lock
    if milestone in {"m2", "m3"}:
        if exec_mode != "inject":
            exec_mode = "inject"
        if backend in {"auto", "megatrain", "mlx-tune", "mlx_tune"}:
            backend = "llama.cpp"
        if gguf_path is None and backend in {"llama.cpp", "llama_cpp", "llama"}:
            gguf_path = _pick_default_gguf()
        args.enable_ortho_kda = True
        args.enable_skvm_verify = True
        if "CGC_M2_STRICT_FINAL" not in os.environ:
            os.environ["CGC_M2_STRICT_FINAL"] = "1"
        if "CGC_M2_REQUIRE_EQ_GATE" not in os.environ:
            os.environ["CGC_M2_REQUIRE_EQ_GATE"] = "1"
        if "CGC_M2_REQUIRE_MEMORY_GATE" not in os.environ:
            os.environ["CGC_M2_REQUIRE_MEMORY_GATE"] = "1"
        if "CGC_M2_REQUIRE_SPEED_GATE" not in os.environ:
            os.environ["CGC_M2_REQUIRE_SPEED_GATE"] = "1"
        if "CGC_M2_REQUIRE_PPL_GATE" not in os.environ:
            os.environ["CGC_M2_REQUIRE_PPL_GATE"] = "1"
        os.environ["CGC_LLAMA_CPU_ALL_VARIANTS"] = "0"
        os.environ["CGC_AUTO_BUILD_CGC_CPP"] = "1"
        require_cuda_env = str(os.environ.get("CGC_REQUIRE_CUDA") or "").strip().lower()
        require_cuda = require_cuda_env in {"1", "true", "yes", "on"}
        if require_cuda:
            if "CGC_LLAMA_NGL" not in os.environ:
                os.environ["CGC_LLAMA_NGL"] = "999"
            if "CGC_LLAMA_BENCH_NGL" not in os.environ:
                os.environ["CGC_LLAMA_BENCH_NGL"] = os.environ["CGC_LLAMA_NGL"]
            if "CGC_LLAMA_PPL_NGL" not in os.environ:
                os.environ["CGC_LLAMA_PPL_NGL"] = os.environ["CGC_LLAMA_NGL"]
        if not bool(getattr(args, "ppl_wikitext2", False)):
            args.ppl_wikitext2 = True
        try:
            default_ctx = "128,512,1024,2048,4096,8192"
            if str(getattr(args, "contexts", "") or "").strip() == default_ctx:
                args.contexts = "2048,4096,8192,16384"
        except Exception:
            pass
    if milestone == "m4":
        os.environ["CGC_M4_SPEEDUP_MIN"] = str(float(getattr(args, "m4_speedup_min", 1.5)))
        os.environ["CGC_M4_REQUIRE_DISTRIBUTED"] = "1"
        if str(os.environ.get("CGC_M4_DISTRIBUTED_SMOKE", "") or "").strip() == "":
            os.environ["CGC_M4_DISTRIBUTED_SMOKE"] = "1"
        if str(getattr(args, "task_type", "inference")) == "inference":
            args.task_type = "train"
        backend = "megatrain"
    if milestone == "m5":
        if exec_mode != "compile":
            exec_mode = "compile"
        if backend in {"auto", "megatrain", "mlx-tune", "mlx_tune"}:
            backend = "llama.cpp"
        if gguf_path is None and backend in {"llama.cpp", "llama_cpp", "llama"}:
            gguf_path = _pick_default_gguf()

    if mode == "mlx-step67":
        input_shape = [int(x) for x in args.input_shape]
        contexts: List[int] = []
        gen_tokens = 0
    else:
        input_shape = [int(x) for x in args.input_shape] if (bool(args.enable_skvm_verify) or bool(args.enable_llm1)) else None
        contexts = [int(x) for x in str(args.contexts).split(",") if str(x).strip()]
        gen_tokens = int(args.gen_tokens)

    if backend == "auto":
        import platform

        sys_name = str(platform.system())
        if mode == "mlx-step67":
            backend = "mlx"
        elif sys_name == "Darwin":
            backend = "mlx"
        else:
            try:
                import torch

                backend = "vllm" if bool(torch.cuda.is_available()) else "llama.cpp"
            except Exception:
                backend = "llama.cpp"

    from cgc_engine.agent.llm_auto_pipeline import LLMAutoPipeline

    ppl_file = str(getattr(args, "ppl_file", "") or "").strip()
    if bool(getattr(args, "ppl_wikitext2", False)) or ppl_file != "":
        os.environ["CGC_LLAMA_PPL_TEST"] = "wikitext2"
    if ppl_file != "":
        os.environ["CGC_LLAMA_PPL_FILE"] = ppl_file
    run_id = str(args.seed)
    try:
        import time as _time

        run_id = f"run_{_time.strftime('%Y%m%d_%H%M%S')}_{int(args.seed)}"
    except Exception:
        run_id = f"run_{int(args.seed)}"

    def _safe_name(s: str) -> str:
        out = []
        for ch in str(s):
            if ch.isalnum() or ch in ("-", "_", "."):
                out.append(ch)
            else:
                out.append("_")
        text = "".join(out).strip("_.")
        return text[:120] if len(text) > 120 else text

    output_dir = str(getattr(args, "output_dir", "") or "").strip()
    if output_dir == "":
        base = Path(project_root).resolve() / "Output" / "PipelineRuns"
        model_tag = _safe_name(gguf_path if backend in ("llama.cpp", "llama_cpp", "llama") else model)
        output_dir = str(base / _safe_name(backend) / model_tag / run_id)

    pipe = LLMAutoPipeline(output_dir=output_dir)
    run_mode = "mlx_step67" if mode == "mlx-step67" else "edge-cloud" if mode == "edge-cloud" else "llm"
    result = pipe.run(
        mode=run_mode,
        exec_mode=exec_mode,
        inject_mode=str(getattr(args, "inject_mode", "attention")),
        task_type=str(getattr(args, "task_type", "inference")),
        backend=backend,
        model=model,
        gguf_path=gguf_path,
        contexts=contexts,
        input_shape=input_shape,
        gen_tokens=gen_tokens,
        warmup_runs=int(args.warmup_runs),
        runs=int(args.runs),
        enable_hooks=bool(args.enable_hooks),
        enable_ortho_kda=bool(args.enable_ortho_kda),
        ortho_kda_base_dim=int(args.ortho_kda_base_dim),
        seed=int(args.seed),
        enable_llm1=bool(args.enable_llm1),
        llm1_base_url=str(args.llm1_base_url),
        llm1_model=str(args.llm1_model),
        llm1_api_key=args.llm1_api_key,
        llm1_timeout_s=int(args.llm1_timeout_s),
        llm1_input_path=str(args.llm1_input_path) if args.llm1_input_path is not None else None,
        enable_fullgraph_aot=bool(args.enable_fullgraph_aot),
        fullgraph_model=str(args.fullgraph_model),
        fullgraph_prompt=str(args.fullgraph_prompt),
        fullgraph_max_new_tokens=int(args.fullgraph_max_new_tokens),
        fullgraph_strict=not bool(args.fullgraph_non_strict),
        enable_skvm_verify=bool(args.enable_skvm_verify),
        skvm_cli=str(args.skvm_cli),
        skvm_auto_install=bool(getattr(args, "skvm_auto_install", False)),
        skvm_input=str(args.skvm_input) if args.skvm_input is not None else None,
        skvm_dtype=str(args.skvm_dtype),
        skvm_timeout_s=int(args.skvm_timeout_s),
        skvm_strict=not bool(args.skvm_non_strict),
        enable_skillvm_aot=bool(getattr(args, "enable_skillvm_aot", False)),
        skillvm_target_model=str(getattr(args, "skillvm_target_model", "") or ""),
        skillvm_compiler_model=str(getattr(args, "skillvm_compiler_model", "") or ""),
        skillvm_adapter=str(getattr(args, "skillvm_adapter", "bare-agent") or "bare-agent"),
        edge_cloud_base_url=str(getattr(args, "edge_cloud_base_url", "") or ""),
        edge_cloud_model=str(getattr(args, "edge_cloud_model", "") or ""),
        edge_cloud_api_key=getattr(args, "edge_cloud_api_key", None),
        edge_cloud_timeout_s=int(getattr(args, "edge_cloud_timeout_s", 120)),
        edge_prompt=str(getattr(args, "edge_prompt", "hello") or "hello"),
        edge_prefill_max_tokens=int(getattr(args, "edge_prefill_max_tokens", 1)),
        enable_mtp=bool(getattr(args, "enable_mtp", False)),
        enable_cuda_graph=bool(getattr(args, "enable_cuda_graph", False)),
        bundle_import_manifest=str(getattr(args, "bundle_import_manifest", "") or ""),
        bundle_import_dir=str(getattr(args, "bundle_import_dir", "") or ""),
        bundle_artifact_base_url=str(getattr(args, "bundle_artifact_base_url", "") or ""),
        mindspeed_base_url=str(getattr(args, "mindspeed_base_url", "") or ""),
        mindspeed_model=str(getattr(args, "mindspeed_model", "") or ""),
        mindspeed_api_key=getattr(args, "mindspeed_api_key", None),
        mindspeed_timeout_s=int(getattr(args, "mindspeed_timeout_s", 120)),
        mindspeed_source_hf=str(getattr(args, "mindspeed_source_hf", "") or ""),
        mindspeed_mcore_dir=str(getattr(args, "mindspeed_mcore_dir", "") or ""),
        mindspeed_precision=str(getattr(args, "mindspeed_precision", "fp8_mixed") or "fp8_mixed"),
        mindspeed_exec_driver=str(getattr(args, "mindspeed_exec_driver", "http") or "http"),
        mindspeed_subprocess_cmd=str(getattr(args, "mindspeed_subprocess_cmd", "") or ""),
        mindspeed_subprocess_cwd=str(getattr(args, "mindspeed_subprocess_cwd", "") or ""),
        mindspeed_subprocess_env_source=str(getattr(args, "mindspeed_subprocess_env_source", "") or ""),
    )

    milestone_rank = {"auto": 0, "m1": 1, "m2": 2, "m3": 3, "m4": 4, "m5": 5, "m6": 6, "m7": 7, "m71": 71, "m72": 72, "m73": 73}
    target_rank = milestone_rank.get(milestone, 0)
    if target_rank >= 6:
        m6_dir = Path(output_dir).resolve() / "m6_product"
        m6_gate = {"status": "FAIL", "reason": "uninitialized"}
        try:
            from cgc_engine.product import build_bundle, run_bundle

            m6_dir.mkdir(parents=True, exist_ok=True)
            build_report = build_bundle(output_dir=str(m6_dir), template="ort_mnist_cpu")
            run_report = run_bundle(output_dir=str(m6_dir))
            b_gate = ((build_report or {}).get("gate_result") or {}).get("m6") if isinstance(build_report, dict) else None
            r_gate = ((run_report or {}).get("gate_result") or {}).get("m6") if isinstance(run_report, dict) else None

            build_status = str((b_gate or {}).get("status") or "")
            run_status = str((r_gate or {}).get("status") or "")
            build_ok = bool(isinstance(b_gate, dict) and build_status in ("PASS", "SKIP"))
            run_ok = bool(isinstance(r_gate, dict) and run_status in ("PASS", "SKIP"))
            ok = bool(build_ok and run_ok)
            overall_status = "PASS" if (build_status == "PASS" and run_status == "PASS") else ("SKIP" if ok else "FAIL")

            m6_gate = {
                "status": str(overall_status),
                "product_dir": str(m6_dir),
                "build_report_path": str(m6_dir / "build_report.json"),
                "run_report_path": str(m6_dir / "run_report.json"),
                "build_bundle_gate": (b_gate or {}).get("build_bundle_gate") if isinstance(b_gate, dict) else None,
                "run_bundle_gate": (r_gate or {}).get("run_bundle_gate") if isinstance(r_gate, dict) else None,
            }
        except Exception as e:
            r = repr(e)
            if isinstance(e, ModuleNotFoundError) and ("onnxruntime" in r or "onnxruntime" in str(e)):
                m6_gate = {"status": "SKIP", "reason": "missing_dependency:onnxruntime", "product_dir": str(m6_dir)}
            else:
                m6_gate = {"status": "FAIL", "reason": f"m6_product_error:{r}", "product_dir": str(m6_dir)}

        try:
            result.steps["m6_product"] = m6_gate
        except Exception:
            pass

        gate_result = getattr(result, "gate_result", None)
        if not isinstance(gate_result, dict):
            gate_result = {"status": "PASS"}
        gate_result["m6"] = m6_gate
        prev_ok = str(gate_result.get("status") or "PASS") == "PASS"
        m6_ok = str(m6_gate.get("status") or "") in ("PASS", "SKIP")
        gate_result["status"] = "PASS" if (prev_ok and m6_ok) else "FAIL"
        setattr(result, "gate_result", gate_result)
        if str(m6_gate.get("status") or "") == "FAIL":
            result.ok = False

    if target_rank >= 7:
        m7_gate = {"status": "FAIL", "reason": "uninitialized"}
        try:
            from cgc_engine.product import run_m7_gate

            m7_report = run_m7_gate(output_dir=str(Path(output_dir).resolve()))
            m7_gate = ((m7_report or {}).get("gate_result") or {}).get("m7") if isinstance(m7_report, dict) else {"status": "FAIL", "reason": "invalid_m7_report"}
        except Exception as e:
            m7_gate = {"status": "FAIL", "reason": f"m7_gate_error:{repr(e)}"}

        try:
            result.steps["m7_industrial"] = m7_gate
        except Exception:
            pass

        gate_result = getattr(result, "gate_result", None)
        if not isinstance(gate_result, dict):
            gate_result = {"status": "PASS"}
        gate_result["m7"] = m7_gate
        prev_ok = str(gate_result.get("status") or "PASS") == "PASS"
        m7_ok = str(m7_gate.get("status") or "") == "PASS"
        gate_result["status"] = "PASS" if (prev_ok and m7_ok) else "FAIL"
        setattr(result, "gate_result", gate_result)
        if str(m7_gate.get("status") or "") != "PASS":
            result.ok = False

    if target_rank >= 71:
        gate_result = getattr(result, "gate_result", None)
        if not isinstance(gate_result, dict):
            gate_result = {"status": "PASS"}
        m7_gate = gate_result.get("m7") if isinstance(gate_result.get("m7"), dict) else {"status": "FAIL", "reason": "missing_m7_gate"}
        gate_result["m71"] = m7_gate
        setattr(result, "gate_result", gate_result)

    if target_rank >= 72:
        m72_gate = {"status": "FAIL", "reason": "uninitialized"}
        try:
            from cgc_engine.product import run_m72_gate

            m72_dir = Path(output_dir).resolve() / "m72_industrial"
            m72_report = run_m72_gate(output_dir=str(m72_dir), cgc_report=result.__dict__)
            m72_gate = ((m72_report or {}).get("gate_result") or {}).get("m72") if isinstance(m72_report, dict) else {"status": "FAIL", "reason": "invalid_m72_report"}
        except Exception as e:
            m72_gate = {"status": "FAIL", "reason": f"m72_gate_error:{repr(e)}"}

        try:
            result.steps["m72_industrial"] = m72_gate
        except Exception:
            pass

        gate_result = getattr(result, "gate_result", None)
        if not isinstance(gate_result, dict):
            gate_result = {"status": "PASS"}
        gate_result["m72"] = m72_gate
        prev_ok = str(gate_result.get("status") or "PASS") == "PASS"
        m72_ok = str(m72_gate.get("status") or "") == "PASS"
        gate_result["status"] = "PASS" if (prev_ok and m72_ok) else "FAIL"
        setattr(result, "gate_result", gate_result)
        if str(m72_gate.get("status") or "") != "PASS":
            result.ok = False

    if target_rank >= 73:
        m73_gate = {"status": "FAIL", "reason": "uninitialized"}
        try:
            from cgc_engine.product import run_m73_gate

            m73_report = run_m73_gate(output_dir=str(Path(output_dir).resolve()))
            m73_gate = ((m73_report or {}).get("gate_result") or {}).get("m73") if isinstance(m73_report, dict) else {"status": "FAIL", "reason": "invalid_m73_report"}
        except Exception as e:
            m73_gate = {"status": "FAIL", "reason": f"m73_gate_error:{repr(e)}"}

        try:
            result.steps["m73_physical"] = m73_gate
        except Exception:
            pass

        gate_result = getattr(result, "gate_result", None)
        if not isinstance(gate_result, dict):
            gate_result = {"status": "PASS"}
        gate_result["m73"] = m73_gate
        prev_ok = str(gate_result.get("status") or "PASS") == "PASS"
        m73_ok = str(m73_gate.get("status") or "") == "PASS"
        gate_result["status"] = "PASS" if (prev_ok and m73_ok) else "FAIL"
        setattr(result, "gate_result", gate_result)
        if str(m73_gate.get("status") or "") != "PASS":
            result.ok = False

    report_path = str(getattr(args, "report_path", "") or "").strip()
    if report_path == "":
        report_path = str(Path(output_dir) / "report.json")
    pipe.write_report(result, report_path)

    bundle_export_dir = str(getattr(args, "bundle_export_dir", "") or "").strip()
    if milestone == "m3" and bundle_export_dir == "":
        bundle_export_dir = str(Path(output_dir) / "bundle_export")
    if bundle_export_dir:
        export_info = pipe.export_bundle(result, bundle_export_dir=bundle_export_dir)
        pipe.write_report(result, report_path)
    print(json.dumps({"ok": bool(result.ok), "output_dir": str(output_dir), "report_path": str(report_path)}, ensure_ascii=False))
    return 0 if result.ok else 1

def add_info_subparser(subparsers):
    """Add 'info' subcommand for system information"""
    parser = subparsers.add_parser(
        'info',
        help='Display CGC Engine system information',
        description='Show version, available backends, and system capabilities',
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        default=False,
        help='Show detailed information',
    )
    parser.set_defaults(func=info_command)

def info_command(args):
    """Execute 'info' subcommand"""
    print("=" * 70)
    print("CGC Engine CLI - MagiCompiler Command Interface")
    print("=" * 70)

    try:
        from cgc_engine import __version__
        print(f"Version: {__version__}")
    except ImportError:
        print("Version: N/A")

    print(f"\nAvailable commands:")
    print(f"  pipeline    - Run unified 8-step pipeline (LLM/MLX)")
    print(f"  info        - Show this information")

    print(f"\n" + "=" * 70)
    print("Backends (Execution Engine)")
    print("=" * 70)
    print(f"  vllm        - vLLM (CUDA) inference engine")
    print(f"  llama.cpp   - llama.cpp GGUF inference")
    print(f"  mlx         - Apple Silicon MLX")
    print(f"  mindspeed   - MindSpeed-LLM OpenAI-compatible endpoint (remote)")

    print(f"\n" + "=" * 70)
    print("Execution Modes (--exec-mode)")
    print("=" * 70)
    print(f"  native      - Original runtime baseline")
    print(f"  inject      - Inject custom backend/hook into runtime")
    print(f"  compile     - Full-graph analyze + compile (.so)")

    print(f"\n" + "=" * 70)
    print("Architecture Flow")
    print("=" * 70)
    print(f"  CLI -> LLMAutoPipeline -> Backend")
    print(f"              |")
    print(f"              v")
    print(f"  [ LLM1 -> SkVM -> FX -> KDA -> AOTInductor -> .so ]")

    if args.verbose:
        print(f"\n" + "=" * 70)
        print("System Capabilities")
        print("=" * 70)
        try:
            import torch
            print(f"  - CUDA available: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"  - CUDA device count: {torch.cuda.device_count()}")
        except ImportError:
            print("  - PyTorch not available")

    print("=" * 60)
    return 0

def create_parser():
    """Create the main argument parser"""
    parser = argparse.ArgumentParser(
        prog='cgc',
        description='CGC Engine CLI - Unified Pipeline Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Architecture:
    CLI -> LLMAutoPipeline -> (LLM1 -> SkVM -> FX -> KDA -> AOTInductor) -> Backend

Examples:
  # 1. Native mode (baseline)
  cgc pipeline --backend vllm --exec-mode native

  # 2. Inject mode (runtime monkey patch / custom backend)
  cgc pipeline --backend llama.cpp --exec-mode inject --enable-ortho-kda

  # 3. Compile mode (LLM1 Translation + SkVM Verify + AOTInductor)
  cgc pipeline --backend mlx --exec-mode compile --enable-llm1 --llm1-input-path /path/to/attn.metal

  # Show info
  cgc info --verbose
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 3.0.0',
    )

    subparsers = parser.add_subparsers(
        title='commands',
        dest='command',
        description='Available commands',
    )

    add_pipeline_subparser(subparsers)
    add_info_subparser(subparsers)

    return parser

def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        return 0

    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())
