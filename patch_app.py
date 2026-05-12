"""Fix two bugs in app.py."""
with open("app.py", encoding="utf-8") as f:
    content = f.read()

# Fix 1: vax_apply_theme -> apply_theme (patch script incorrectly renamed it)
content = content.replace("vax_apply_theme(", "apply_theme(")

# Fix 2: bad sort_values lambda in build_risk
old = 'high_risk = high_risk.sort_values(lambda x: x["Risk"].map(risk_order) if False else "ActiveCases", ascending=False).head(20)'
new = 'high_risk = high_risk.sort_values("ActiveCases", ascending=False).head(20)'
content = content.replace(old, new)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fix 1 (vax_apply_theme):", "vax_apply_theme" not in content)
print("Fix 2 (sort_values lambda):", 'sort_values(lambda' not in content)
