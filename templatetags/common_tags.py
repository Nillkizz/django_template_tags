# Docs https://github.com/Nillkizz/django_template_tags
from django.template import Library, Node, NodeList
from django.template.defaulttags import CycleNode
from django.template.base import TemplateSyntaxError
from django.utils.safestring import SafeString


register = Library()


class MultiplierRender(Node):
    def __init__(self, nodelist, ratio):
        self.nodelist = nodelist
        self.ratio = ratio

    def render(self, context):
        content = ''
        for _ in range(self.ratio):
            content += self.nodelist.render(context)
        return content


class OrRender(Node):
    def __init__(self, values):
        self.values = values

    def render(self, context):
        condition = ''
        vars = {'content': ''}
        for i, value in enumerate(self.values):
            value = value.strip()
            if value.startswith(('"', '\'')) and value.endswith(('"', '\'')):
                value = value.strip('"').strip("'")
                condition += f'"{value}" or '
                continue
            key = value.split('.')[0]
            if var := context.get(key):
                if type(var) is dict:
                    query = '["' + query[0] + '"]'if (query := value.split('.')[1:]) else ''
                else:
                    query = '.' + '.'.join(query) if (query := value.split('.')[1:]) else ''

                condition += f'vars["value_{i}"] or '
                vars['value_0'] = 123
                exec(f'vars["value_{i}"] = var{query}')

        condition = condition.strip(' or ')
        exec(f'vars["content"] = {condition}')
        content = str(vars['content'])
        return content


@register.tag(name='or')
def do_or_render(parser, token):
    bits = token.split_contents()[1:]
    return OrRender(bits)


@register.tag
def multiply(parser, token):
    bits = token.split_contents()
    ratio = int(bits[1])
    nodelist = parser.parse(('endmultiply', None))
    parser.next_token()
    return MultiplierRender(nodelist, ratio)


@register.tag(name='range')
def do_range(parser, token):
    args = token.split_contents()

    as_form = False
    if len(args) > 3:
        # {% cycle ... as foo [silent] %} case.
        if args[-3] == "as":
            if args[-1] != "silent":
                raise TemplateSyntaxError("Only 'silent' flag is allowed after range cycle's name, not '%s'." % args[-1])
            as_form = True
            silent = True
            args = args[:-1]
        elif args[-2] == "as":
            as_form = True
            silent = False

    if as_form:
        name = args[-1]
        values = [parser.compile_filter(arg) for arg in args[1:-2]]
        node = CycleNode(values, name, silent=silent)
        if not hasattr(parser, '_named_cycle_nodes'):
            parser._named_cycle_nodes = {}
        parser._named_cycle_nodes[name] = node
    elif len(args) < 5:
        values = [parser.compile_filter(str(arg)) for arg in range(*[int(arg) for arg in args[1:]])]
        node = CycleNode(values)
    else:
        raise TemplateSyntaxError('Range allowed only 3 args: (start, stop, step)')

    return node
