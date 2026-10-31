#!/usr/bin/env python3
"""asr-falls asr-card: render the measurement configuration behind a reported ASR.

Usage:
  python asr_card.py --config card_config.yaml [--out card.md]

The config names the judge(s), calibration version, protocol, truncation,
binarization threshold, and sample size. The card renders against the clause
slots of T/ISC 0146-2026 (9.7/11.3/11.5), the EU AI Act Art.55 evaluation
obligation, and NIST AI 600-1 MS-2.8-002. A filled example config ships as
card_config.example.yaml.
"""
import argparse, json

SLOTS = [
    ("judge_identity", "Judge (model + provider)", "T/ISC 0146-2026 §11.3"),
    ("judge_calibration", "Calibration (tpr/fpr/CI + calibration-set provenance)", "T/ISC §9.7"),
    ("protocol", "System prompt / protocol variant", "T/ISC §11.5"),
    ("truncation", "Judge input truncation (chars)", "NIST AI 600-1 MS-2.8-002"),
    ("binarization", "Binarization threshold and scorer version", "NIST AI 600-1"),
    ("sample", "Behaviors n, seeds, sampling scheme", "EU AI Act Art.55 evaluation record"),
    ("correction", "Corrected-ASR fields and CI method", "EU AI Act Art.55 evaluation record"),
    ("abstention", "Abstention / triage zone assignment if used", "internal"),
]

def load(path):
    txt = open(path).read()
    try:
        import yaml
        return yaml.safe_load(txt)
    except Exception:
        return json.loads(txt)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="card.md")
    args = ap.parse_args()
    cfg = load(args.config)
    lines = ["# ASR-Card", "",
             f"measurement_id: {cfg.get('measurement_id', 'unnamed')}",
             f"calibration_version: {cfg.get('calibration_version', 'unspecified')}", ""]
    lines += ["| slot | value | mapped clause |", "|---|---|---|"]
    for key, label, clause in SLOTS:
        lines.append(f"| {label} | {cfg.get(key, 'NOT STATED')} | {clause} |")
    missing = [k for k, _, _ in SLOTS if not cfg.get(k)]
    if missing:
        lines += ["", f"**UNSTATED SLOTS ({len(missing)}):** " + ", ".join(missing) +
                  " — a reported ASR with unstated slots is not comparable across papers."]
    else:
        lines += ["", "All slots stated: this ASR is comparable under the stated configuration."]
    open(args.out, "w").write("\n".join(lines) + "\n")
    print(f"card written: {args.out} ({len(SLOTS) - len(missing)}/{len(SLOTS)} slots stated)")

if __name__ == "__main__":
    main()
