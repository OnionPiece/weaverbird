import os

templates_path = os.path.dirname(__file__)
model_template_name = 'model.j2'

__all__ = [
    mod[:-3] for mod in os.listdir(templates_path)
    if mod.endswith('.py') and mod not in ('__init__.py', 'utils.py')
    ]
