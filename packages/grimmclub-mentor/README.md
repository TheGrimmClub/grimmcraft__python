# grimmclub-mentor

Turn diagnostics into teaching: an explanation, a lesson, a link.

```python
mentor = Mentor(lesson_root="grimmoire")
mentor.learn_from()          # explanations from the teaching material
mentor.report(result.diagnostics)
```

Generic on purpose — nothing here knows what any diagnostic code means. Codes are
opaque strings and explanations are *registered* into the model, from Python or
from Markdown in the teaching repository. Domain packages extend the mentor; the
mentor never reaches into them, which is what will let this package move to a
repository of its own as a move rather than a rewrite.

A missing teaching repository is not an error: the mentor explains what it has
and stays quiet about the rest.
