import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSACTIONS = ROOT / "config" / "transactions"


def build_transaction_manifest(architecture, page):
    """Build a cold-navigation HTTP transaction from a real browser trace."""
    folder = ROOT / "results" / architecture.lower() / page.lower()
    reports = sorted(folder.glob("*.json"), key=lambda path: path.stat().st_mtime)
    if not reports:
        raise RuntimeError(
            f"No Lighthouse report for {architecture}/{page}. "
            "Run --phase lighthouse before k6 or costs."
        )
    report_path = reports[-1]
    with report_path.open("r", encoding="utf-8") as handle:
        report = json.load(handle)

    items = report.get("audits", {}).get("network-requests", {}).get(
        "details", {}).get("items", [])
    requests = []
    seen = set()
    for item in items:
        url = item.get("url")
        status = int(item.get("statusCode", 0) or 0)
        if not url or not url.startswith(("http://", "https://")) or status >= 400:
            continue
        if url in seen:
            continue
        seen.add(url)
        requests.append({"url": url, "resource_type": item.get("resourceType", "Other")})

    if not requests or requests[0]["resource_type"] != "Document":
        raise RuntimeError(f"No document request in {architecture}/{page} trace")

    payload = {
        "architecture": architecture,
        "page": page,
        "model": "cold navigation reconstructed from Lighthouse network trace",
        "source_report": str(report_path.relative_to(ROOT)),
        "requests": requests,
    }
    output = TRANSACTIONS / architecture.lower() / f"{page.lower()}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return output, payload


def ensure_transaction_manifests():
    generated = {}
    for architecture in ("SPA", "SSR"):
        for page in ("Dashboard", "Inventory", "Sales"):
            generated[(architecture, page)] = build_transaction_manifest(architecture, page)
    return generated
