import re


def load_prompt(path: str) -> str:
	with open(path, "r", encoding="utf-8") as f:
		return f.read()


def render_prompt(template: str, variables: dict[str, str]) -> str:
	# Replace {{ var }} style tokens with values
	def replacer(match: re.Match) -> str:
		name = match.group(1).strip()
		return str(variables.get(name, ""))
	pattern = re.compile(r"\{\{\s*([^}]+)\s*\}\}")
	return pattern.sub(replacer, template)
