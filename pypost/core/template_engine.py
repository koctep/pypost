from jinja2 import Template

class TemplateEngine:
    @staticmethod
    def render(content: str, variables: dict) -> str:
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
            template = Template(content)
            return template.render(**variables)
        except Exception as e:
            # In case of error (e.g. invalid syntax), return original content or log
            print(f"Template rendering error: {e}")
            return content
