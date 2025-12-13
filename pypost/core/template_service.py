from jinja2 import Environment

class TemplateService:
    def __init__(self):
        self.env = Environment()

    def render_string(self, content: str, variables: dict) -> str:
        """
        Renders a string template with provided variables using Jinja2.

        Args:
            content: The string containing variables like {{ var_name }}
            variables: A dictionary of variable names and values

        Returns:
            The rendered string with variables substituted.
        """
        if not content:
            return ""

        try:
            template = self.env.from_string(content)
            return template.render(**variables)
        except Exception as e:
            # In case of error (e.g. invalid syntax), return original content or log
            print(f"Template rendering error: {e}")
            return content

    def parse(self, content: str):
        """
        Parses the content into an AST.
        """
        return self.env.parse(content)

# Global instance
template_service = TemplateService()
