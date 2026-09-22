"""
TIME Protocol - Simple Template Engine
Zero-dependency template rendering with {{ variable }} substitution.
"""

import re
import html
from typing import Dict, Any


class TemplateEngine:
    """
    Minimal template engine supporting:
    - {{ variable }} substitution
    - {{ variable|escape }} HTML escaping
    - {% for item in items %} ... {% endfor %} basic loops
    - {% if condition %} ... {% endif %} basic conditionals
    """
    
    VARIABLE_PATTERN = re.compile(r'\{\{\s*([^}]+?)\s*\}\}')
    FOR_PATTERN = re.compile(
        r'\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}',
        re.DOTALL
    )
    IF_PATTERN = re.compile(
        r'\{%\s*if\s+([^%]+?)\s*%\}(.*?)\{%\s*endif\s*%\}',
        re.DOTALL
    )
    
    def __init__(self, template_string: str):
        self.template = template_string
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render the template with the given context."""
        result = self.template
        # Handle for loops first (they may contain variables)
        result = self._render_for_loops(result, context)
        # Handle if conditionals
        result = self._render_if_blocks(result, context)
        # Handle plain variables last
        result = self._render_variables(result, context)
        return result
    
    def _render_variables(self, text: str, context: Dict[str, Any]) -> str:
        def replacer(match):
            expr = match.group(1).strip()
            
            # Support filters like {{ x|escape }}
            if '|' in expr:
                var_name, filter_name = [p.strip() for p in expr.split('|', 1)]
                value = self._resolve(var_name, context)
                if filter_name == 'escape':
                    return html.escape(str(value))
                return str(value)
            
            value = self._resolve(expr, context)
            return str(value)
        
        return self.VARIABLE_PATTERN.sub(replacer, text)
    
    def _resolve(self, expr: str, context: Dict[str, Any]) -> Any:
        """Resolve dotted paths like 'block.hash'."""
        parts = expr.split('.')
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, '')
            else:
                value = getattr(value, part, '')
            if value == '':
                break
        return value
    
    def _render_for_loops(self, text: str, context: Dict[str, Any]) -> str:
        """Handle simple for loops (non-nested)."""
        while True:
            match = self.FOR_PATTERN.search(text)
            if not match:
                break
            
            item_name = match.group(1)
            list_name = match.group(2)
            body = match.group(3)
            
            items = context.get(list_name, [])
            rendered_parts = []
            
            for item in items:
                item_context = dict(context)
                if isinstance(item, dict):
                    item_context[item_name] = item
                else:
                    item_context[item_name] = item
                
                # Render body for each item
                rendered_item = self._render_variables(body, item_context)
                rendered_parts.append(rendered_item)
            
            text = text[:match.start()] + "".join(rendered_parts) + text[match.end():]
        
        return text
    
    def _render_if_blocks(self, text: str, context: Dict[str, Any]) -> str:
        """Handle simple if blocks."""
        while True:
            match = self.IF_PATTERN.search(text)
            if not match:
                break
            
            condition = match.group(1).strip()
            body = match.group(2)
            
            # Simple truthy evaluation
            value = self._resolve(condition, context)
            if value:
                text = text[:match.start()] + body + text[match.end():]
            else:
                text = text[:match.start()] + text[match.end():]
        
        return text


def render_template(template_string: str, context: Dict[str, Any]) -> str:
    """Convenience function."""
    return TemplateEngine(template_string).render(context)
