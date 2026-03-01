def render_md(pkg: dict) -> str:
    m = pkg["meta"]
    p = pkg["problem"]
    s = pkg["scope"]

    lines = []
    lines.append(f"# {m['title']}")
    lines.append("")
    lines.append(f"- **Agent:** Requirements Intake Agent")
    lines.append(f"- **ID:** {m['id']}")
    lines.append(f"- **Version:** {m.get('version','v1')} | **Status:** {m.get('status','draft')}")
    lines.append(f"- **Sensitivity:** {m['classification']['sensitivity']} | **Domain:** {m['classification']['domain']}")
    lines.append("")
    lines.append("## Problem")
    lines.append(p["context"])
    lines.append("")
    lines.append("**Pain points:**")
    for x in p["pain_points"]:
        lines.append(f"- {x}")
    lines.append("")
    lines.append(f"**Goal:** {p['goal']}")
    lines.append("")
    lines.append("**Success definition:**")
    for x in p["success_definition"]:
        lines.append(f"- {x}")
    lines.append("")
    lines.append("## Scope")
    lines.append("**In scope:**")
    for x in s["in_scope"]:
        lines.append(f"- {x}")
    lines.append("")
    lines.append("**Out of scope:**")
    for x in s["out_of_scope"]:
        lines.append(f"- {x}")
    lines.append("")
    lines.append("## Requirements")
    for r in pkg["requirements"]:
        lines.append(f"### {r['id']} ({r['priority']})")
        lines.append(r["statement"])
        lines.append(f"- Type: {r['type']}")
        lines.append(f"- Rationale: {r['rationale']}")
        lines.append(f"- Evidence: {r['evidence']['source_ref']} — {r['evidence']['source_excerpt']}")
        lines.append("")
    lines.append("## Acceptance criteria")
    for ac in pkg["acceptance_criteria"]:
        lines.append(f"- **{ac['id']}** {ac['criterion']} (refs: {', '.join(ac['linked_requirements'])})")
    lines.append("")
    lines.append("## Open questions")
    for q in pkg["open_questions"]:
        lines.append(f"- **{q['id']}** {q['question']} (target: {q['target']}, status: {q['status']})")
    lines.append("")
    lines.append("## Risks")
    for rk in pkg["risks"]:
        lines.append(f"- **{rk['id']}** {rk['risk']} (impact: {rk['impact']}, likelihood: {rk['likelihood']}) | Mitigation: {rk['mitigation']}")
    lines.append("")
    lines.append("## LLM trace")
    tr = m["llm_trace"]
    lines.append(f"- provider/model: {tr.get('provider')}/{tr.get('model')}")
    lines.append(f"- tokens in/out: {tr.get('tokens_in')}/{tr.get('tokens_out')}")
    lines.append(f"- cost_estimate: {tr.get('cost_estimate')}")
    return "\n".join(lines)
