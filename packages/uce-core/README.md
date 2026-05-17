# uce-core

Pydantic schema, YAML loader, and validator for Universal Competency Engine competencies.

```python
from uce_core import load_competency

comp = load_competency("competencies/procurement/competency.yaml")
print(comp.name, "—", len(comp.skills), "skills")
```
