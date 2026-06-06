import json
from pathlib import Path
from typing import Any, Dict
import yaml


def _as_float(x: Any, default: float) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def run_m72_gate(*, output_dir: str, cgc_report: Dict[str, Any]) -> Dict[str, Any]:
    out_dir_p = Path(output_dir).expanduser().resolve()
    out_dir_p.mkdir(parents=True, exist_ok=True)

    cfg_path = (Path(__file__).resolve().parents[1] / "agent" / "eval" / "m72_gate.yaml").resolve()
    with open(str(cfg_path), "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    report = cgc_report if isinstance(cgc_report, dict) else {}
    m7_data = (report.get("gate_result") or {}).get("m7", {})
    if not isinstance(m7_data, dict) or not m7_data:
        gate = {"status": "FAIL", "reason": "missing_gate_result.m7", "config": str(cfg_path)}
        out_file = str(out_dir_p / "report.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"name": config.get("name"), "status": "FAIL", "metrics": {}}, f, ensure_ascii=False, indent=2)
        return {"gate_result": {"m72": gate}, "report_path": out_file}

    final_pass = True
    results: Dict[str, str] = {}

    for metric_group in (config.get("metrics") or []):
        group_name = str(metric_group.get("name") or "")
        rules = metric_group.get("rules") or []
        group_pass = True

        for rule in rules:
            metric_id = str(rule.get("metric") or "")
            op = str(rule.get("operator") or "")
            threshold = _as_float(rule.get("threshold"), 0.0)
            actual_value = None

            if group_name == "dynamic_trace_l1":
                dt = m7_data.get("dynamic_trace_l1", {})
                if not isinstance(dt, dict) or not dt:
                    dt = m7_data.get("dynamic_trace", {})
                if not isinstance(dt, dict):
                    dt = {}

                compile_variants = dt.get("compile_variants", []) if isinstance(dt.get("compile_variants"), list) else []
                correctness = dt.get("correctness", []) if isinstance(dt.get("correctness"), list) else []

                if metric_id == "compile_success_rate":
                    if "compile_success_rate" in dt:
                        actual_value = _as_float(dt.get("compile_success_rate"), 0.0)
                    else:
                        ok = 0
                        for x in compile_variants:
                            if isinstance(x, dict) and str(x.get("status") or "") == "PASS":
                                ok += 1
                        actual_value = float(ok / len(compile_variants)) if len(compile_variants) > 0 else 0.0
                elif metric_id == "cache_hit_rate":
                    if "cache_hit_rate" in dt:
                        actual_value = _as_float(dt.get("cache_hit_rate"), 0.0)
                    else:
                        hit = 0
                        for x in compile_variants:
                            if isinstance(x, dict) and bool(x.get("cache_hit")):
                                hit += 1
                        actual_value = float(hit / len(compile_variants)) if len(compile_variants) > 0 else 0.0
                elif metric_id == "correctness_consistency":
                    if "correctness_consistency" in dt:
                        actual_value = _as_float(dt.get("correctness_consistency"), 0.0)
                    else:
                        ok = 0
                        for x in correctness:
                            if isinstance(x, dict) and bool(x.get("repeat_consistent")):
                                ok += 1
                        actual_value = float(ok / len(correctness)) if len(correctness) > 0 else 0.0

            elif group_name == "state_compression":
                sc = m7_data.get("state_compression", {})
                if not sc:
                    sc = m7_data.get("state_compression_summary", {})
                if not isinstance(sc, dict):
                    sc = {}
                if metric_id == "compression_ratio":
                    actual_value = sc.get("compression_ratio", 1.0)
                elif metric_id == "restore_consistency":
                    actual_value = sc.get("restore_consistency", 0.0)
                elif metric_id == "dedup_expansion_ratio":
                    actual_value = sc.get("dedup_expansion_ratio", 999.0)

            elif group_name == "soft_rt_replay":
                rp = m7_data.get("soft_rt_replay", {})
                if not rp:
                    rp = m7_data.get("replay", {})
                if not isinstance(rp, dict):
                    rp = {}
                if metric_id == "deadline_ms":
                    actual_value = rp.get("deadline_ms", 999.0)
                elif metric_id == "p99_latency_ms":
                    if "p99_latency_ms" in rp:
                        actual_value = rp.get("p99_latency_ms", 999.0)
                    else:
                        lat = rp.get("latency_ms")
                        actual_value = (lat.get("p99") if isinstance(lat, dict) else 999.0)
                elif metric_id == "miss_rate":
                    actual_value = rp.get("miss_rate", 1.0)

            elif group_name == "industrial_audit":
                au = m7_data.get("industrial_audit", {})
                if not au:
                    a2 = m7_data.get("audit", {})
                    if isinstance(a2, dict):
                        au = {
                            "event_integrity": 1.0 if str(a2.get("status") or "") == "PASS" else 0.0,
                            "hash_chain_valid": 1.0 if bool(a2.get("verify_ok")) else 0.0,
                        }
                if not isinstance(au, dict):
                    au = {}
                if metric_id == "event_integrity":
                    actual_value = au.get("event_integrity", 0.0)
                elif metric_id == "hash_chain_valid":
                    actual_value = au.get("hash_chain_valid", 0.0)

            if actual_value is None:
                group_pass = False
                continue

            av = _as_float(actual_value, 0.0)
            passed = False
            if op == ">=":
                passed = av >= threshold
            elif op == "<=":
                passed = av <= threshold
            elif op == "==":
                passed = av == threshold
            if not passed:
                group_pass = False

        results[group_name] = "PASS" if group_pass else "FAIL"
        if not group_pass:
            final_pass = False

    out_file = str(out_dir_p / str((config.get("output") or {}).get("report_file") or "report.json"))
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"name": config.get("name"), "status": "PASS" if final_pass else "FAIL", "metrics": results}, f, ensure_ascii=False, indent=2)

    gate = {"status": "PASS" if final_pass else "FAIL", "config": str(cfg_path), "report_path": out_file, "metrics": results}
    return {"gate_result": {"m72": gate}, "report_path": out_file}

