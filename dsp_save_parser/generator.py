# parser generator

# save data parsing grammar
# ver 1.0.2
# COMMENT ::= "//" [^\n]*
# (COMMENT can placed everywhere at the end of line)
# DOCUMENT ::= ([NEW_LINE] CLASS_DEF)*
# NEW_LINE ::= [SPACE] [COMMENT] "\n" [NEW_LINE]
# SPACE ::= [ \t]+
# CLASS_DEF ::= TOKEN [SPACE] [NEWLINE] "{" NEWLINE CLASS_BODY "}" [NEWLINE]
# TOKEN ::= [A-Za-z_] [A-Za-z0-9_]*
# CLASS_BODY ::= [ATTRIBUTE_DEF [NEWLINE ATTRIBUTE_DEF]*]
# ATTRIBUTE_DEF ::= (INJECTED_VARIABLE_DEF | VARIABLE_DEF) [SPACE] [INLINE_COMMENT]
# INJECTED_VARIABLE_DEF ::= "injected" SPACE VARIABLE_DEF
# VARIABLE_DEF ::= VARIABLE_TYPE SPACE TOKEN [SPACE] [ARRAY_DEF] [SPACE] [IF_CLAUSE] [SPACE] [PROPS_CLAUSE] [SPACE]
#                  [DEFAULT_CLAUSE] [SPACE] [ASSERTION]
# INLINE_COMMENT ::= COMMENT
# VARIABLE_TYPE ::= TOKEN
# ARRAY_DEF ::= "[" [SPACE] ARRAY_SIZE [SPACE] "]"
# ARRAY_SIZE ::= [^\]]+
# IF_CLAUSE ::= "if" [SPACE] "(" [SPACE] CONDITION [SPACE] ")"
# CONDITION ::= [^\)]+
# PROPS_CLAUSE ::= "props" [SPACE] "(" [SPACE] PROPS_BODY [SPACE] ")"
# PROPS_BODY ::= PROPS_ITEM [SPACE] "," [SPACE] PROPS_BODY
# PROPS_ITEM ::= [^\)]+
# DEFAULT_CLAUSE ::= "default" [SPACE] "(" [SPACE] (VALUE | TOKEN) [SPACE] ")"
# ASSERTION ::= "=" [SPACE] (VALUE | TOKEN)
# VALUE ::= NUMERIC_VALUE | STRING_VALUE
# NUMERIC_VALUE ::= "-"? (INTEGER_VALUE | FLOAT_VALUE)
# INTEGER_VALUE ::= ([0-9]+ | "0x" [0-9a-fA-F]+)
# FLOAT_VALUE ::= [0-9]+ "." [0-9]*
# STRING_VALUE ::= "\"" [^"]* "\""

# NOTE: for "injected" fields, the value is passed by "props" from the parse chain instead of parsing from stream
# example for how to use "injected" and "props":
# MyClass {
#   int32 id[5]
#   string name
#   OtherClass other[5] props (id[i], name)  // use "i" to obtain the index inside an array
# }
# OtherClass {
#   injected int32 id = 0  // the first (start from 0) element passed from "props"
#   injected string name = 1  // the second (start from 0) element passed from "props"
#   int32 otherFields  // normal field, the value will be parsed from stream: read 4 bytes, then cast to int32
# }

from typing import *
from typing import TextIO
import re
import hashlib
import os
from datetime import datetime
from io import StringIO


SPACES = re.compile(r'[ \t]*')
SPACE = re.compile(r'[ \t]')
TOKEN = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
ARRAY_SIZE = re.compile(r'\s*([^]]+)\s*')
CONDITION = re.compile(r'if\s*\(\s*([^)]+)\s*\)')
DEFAULT_CLAUSE = re.compile(r'default\s*\(\s*([^)]+)\s*\)')
PROPS_BODY = re.compile(r'props\s*\(\s*([^)]+)\s*\)')

BUILTIN_TYPES = {'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'float32', 'float64',
                 'string', 'boolean', 'FlexibleInt'}
FLOAT_COMPARISON_EPS = 1e-6


# convert camel variable like varName to var_name
def camel_to_underline(name: str):
    ret = re.sub(r'([A-Z])', r'_\1', name).lower()
    # remove leading "_"
    if ret.startswith('_'):
        ret = ret[1:]
    # replace the stub "!= null" and "== null" to python "is not None" and "is None"
    ret = re.sub(r'==\s*null', r' is None', ret)
    ret = re.sub(r'!=\s*null', r' is not None', ret)
    # remove unnecessary spaces
    ret = re.sub(r'\s+', ' ', ret)
    return ret


def parse_comment(def_file: TextIO, out_py_file: TextIO, line_no: int = 0):
    line = def_file.readline().rstrip()
    assert line.startswith('//'), 'line %d: %s' % (line_no, line)
    line = line[2:]
    if SPACE.match(line):
        # only skip the first space
        line = line[1:]
    # write to generated python file
    out_py_file.write('# (L%d): %s\n' % (line_no, line))
    return line_no + 1


def parse_array_def(def_file: TextIO, var_attrs: Dict[str, Any], line_no: int):
    rollback_position = def_file.tell()
    line = def_file.readline()
    if line.startswith('['):
        line = line[1:]
        rollback_position += 1
        match = ARRAY_SIZE.match(line)
        assert match, 'line %d: %s' % (line_no, line)
        array_size = match.group(1)
        line = line[match.end():]
        rollback_position += match.end()
        assert line.startswith(']'), 'line %d: %s' % (line_no, line)
        rollback_position += 1
        var_attrs['is_array'] = True
        var_attrs['array_size'] = array_size
    else:
        var_attrs['is_array'] = False
    def_file.seek(rollback_position)
    return line_no


def parse_if_clause(def_file: TextIO, var_attrs: Dict[str, Any], line_no: int):
    rollback_position = def_file.tell()
    line = def_file.readline()
    def_file.seek(rollback_position)
    if line.startswith('if'):
        match = CONDITION.match(line)
        assert match, 'line %d: %s' % (line_no, line)
        condition = match.group(1)
        rollback_position += match.end()
        var_attrs['if_clause'] = condition
    else:
        var_attrs['if_clause'] = None
    def_file.seek(rollback_position)
    return line_no


def parse_default_clause(def_file: TextIO, var_attrs: Dict[str, Any], line_no: int):
    rollback_position = def_file.tell()
    line = def_file.readline()
    def_file.seek(rollback_position)
    if line.startswith('default'):
        match = DEFAULT_CLAUSE.match(line)
        assert match, 'line %d: %s' % (line_no, line)
        default_value = match.group(1).strip()
        if TOKEN.match(default_value):
            var_attrs['default'] = {'type': 'ref', 'value': default_value}
        else:
            tmp_rollback_position = rollback_position + match.start(1)
            def_file.seek(tmp_rollback_position)
            tmp = {}
            line_no = parse_value(def_file, tmp, line_no)
            var_attrs['default'] = {'type': 'const', 'value': tmp['value']}
        rollback_position += match.end()
    else:
        var_attrs['default'] = None
    def_file.seek(rollback_position)
    return line_no


def parse_value(def_file: TextIO, var_attrs: Dict[str, Any], line_no: int):
    rollback_position = def_file.tell()
    line = def_file.readline()
    def_file.seek(rollback_position)
    if line.startswith('"'):
        # string value
        line = line[1:]
        another_quote_pos = line.find('"')
        assert another_quote_pos != -1, 'line %d: %s' % (line_no, line)
        var_attrs['value'] = line[:another_quote_pos]
        rollback_position += another_quote_pos + 2
    else:
        # numeric value
        if not re.search(r'-?[0-9]', line):
            # skip non-numeric value
            def_file.seek(rollback_position)
            return line_no
        sign = line.startswith('-')
        if sign:
            line = line[1:]
            rollback_position += 1
        if line.startswith('0x'):
            line = line[2:]
            rollback_position += 2
            match = re.search(r'[0-9a-fA-F]+', line)
            assert match, 'line %d: %s' % (line_no, line)
            var_attrs['value'] = int(match.group(0), 16)
            rollback_position += match.end()
        else:
            match = re.search(r'[0-9]+', line)
            assert match, 'line %d: %s' % (line_no, line)
            group1 = match.group(0)
            value_type = int
            rollback_position += match.end()
            line = line[match.end():]
            if line.startswith('.'):
                value_type = float
                line = line[1:]
                rollback_position += 1
                match = re.search(r'[0-9]+', line)
                if match:
                    group2 = match.group(0)
                    rollback_position += match.end()
                    group = '%s.%s' % (group1, group2)
                else:
                    group = group1
            else:
                group = group1
            var_attrs['value'] = value_type(group)
        if sign:
            var_attrs['value'] = -var_attrs['value']
    var_attrs['type'] = 'const'
    def_file.seek(rollback_position)
    return line_no


def parse_assertion(def_file: TextIO, var_attrs: Dict[str, Any], line_no: int):
    rollback_position = def_file.tell()
    line = def_file.readline()
    def_file.seek(rollback_position)
    if line.startswith('='):
        line = line[1:]
        rollback_position += 1
        match = SPACES.match(line)
        rollback_position += match.end()
        line = line[match.end():]
        def_file.seek(rollback_position)
        match = TOKEN.match(line)
        if match:
            var_attrs['assertion'] = {'type': 'ref', 'value': match.group(0)}
            rollback_position += match.end()
            def_file.seek(rollback_position)
        else:
            attrs = {}
            line_no = parse_value(def_file, attrs, line_no)
            var_attrs['assertion'] = attrs
    else:
        var_attrs['assertion'] = None
    return line_no


def parse_props_clause(def_file: TextIO, var_attrs: Dict[str, Any], line_no: int):
    rollback_position = def_file.tell()
    line = def_file.readline()
    def_file.seek(rollback_position)
    if line.startswith('props'):
        match = PROPS_BODY.match(line)
        assert match, 'line %d: %s' % (line_no, line)
        props_body = match.group(1).strip()
        props_body = props_body.split(',')
        props_body = [x.strip() for x in props_body]
        var_attrs['props'] = props_body
        rollback_position += match.end()
    else:
        var_attrs['props'] = None
    def_file.seek(rollback_position)
    return line_no


def parse_variable_def(def_file: TextIO, var_meta: Dict[str, Any], line_no: int):
    rollback_position = def_file.tell()
    line = def_file.readline().rstrip()

    match = TOKEN.match(line)
    assert match, 'line %d: %s' % (line_no, line)
    var_type = match.group()
    line = line[match.end():]
    rollback_position += match.end()
    spaces = SPACES.match(line)
    assert spaces.end() > 0, 'line %d: %s' % (line_no, line)
    line = line[spaces.end():]
    rollback_position += spaces.end()

    match = TOKEN.match(line)
    assert match, 'line %d: %s' % (line_no, line)
    var_name = match.group()
    line = line[match.end():]
    rollback_position += match.end()
    spaces = SPACES.match(line)
    rollback_position += spaces.end()

    var_meta['type'] = var_type
    var_meta['name'] = var_name

    def_file.seek(rollback_position)
    line_no = parse_array_def(def_file, var_meta, line_no)

    extra_defs = {'if_clause': parse_if_clause, 'default': parse_default_clause, 'assertion': parse_assertion,
                  'props': parse_props_clause}
    while True:
        rollback_position = def_file.tell()
        line = def_file.readline().rstrip('\n')
        spaces = SPACES.match(line)
        rollback_position += spaces.end()
        line = line[spaces.end():]
        if len(line) == 0:
            for key in extra_defs:
                if key not in var_meta:
                    var_meta[key] = None
            break

        def_file.seek(rollback_position)
        matched = False
        for key, handling_func in extra_defs.items():
            if var_meta.get(key, None) is None:
                line_no = handling_func(def_file, var_meta, line_no)
                if var_meta.get(key, None) is not None:
                    matched = True
                    break
        if not matched:
            return line_no

    def_file.seek(rollback_position)
    return line_no


def parse_attribute_def(def_file: TextIO, class_attrs: Dict[str, Any], line_no: int):
    var_meta = {}

    # 1.0.2: injected keyword
    rollback_position = def_file.tell()
    line = def_file.readline().rstrip('\n')
    if line.startswith('injected'):
        var_meta['injected'] = True
        line = line[8:]
        rollback_position += 8
        match = SPACES.match(line)
        rollback_position += match.end()
    else:
        var_meta['injected'] = False

    def_file.seek(rollback_position)
    line_no = parse_variable_def(def_file, var_meta, line_no)

    rollback_position = def_file.tell()
    line = def_file.readline().rstrip('\n')
    spaces = SPACES.match(line)
    rollback_position += spaces.end()
    line = line[spaces.end():]

    # inline comment
    if line.startswith('//'):
        comment = line[2:]
        if SPACE.search(comment):
            comment = comment[1:]
        var_meta['comment'] = comment
        rollback_position += len(line)
    else:
        var_meta['comment'] = None

    def_file.seek(rollback_position)
    class_attrs[var_meta['name']] = var_meta
    return line_no


def parse_class_body(def_file: TextIO, class_attrs: Dict[str, Any], line_no: int):
    tmp_comment_index = 0
    while True:
        rollback_position = def_file.tell()
        if def_file.read(1) == '}':
            def_file.seek(rollback_position)
            return line_no
        def_file.seek(rollback_position)
        line_no = parse_attribute_def(def_file, class_attrs, line_no)
        tmp_comment = StringIO()
        line_no = parse_new_line(def_file, tmp_comment, line_no)
        if tmp_comment.tell() > 0:
            class_attrs['tmp_comment_%d' % tmp_comment_index] = {'type': 'comment', 'comment': tmp_comment.getvalue()}


def pretty_write(out_py_file: TextIO, array: List[str], leading_str: str = '', leading_spaces: int = -1,
                 trailing_str: str = '', trailing_spaces: int = -1, max_width: int = 120):
    if leading_spaces == -1:
        leading_spaces = len(leading_str)
    if trailing_spaces == -1:
        trailing_spaces = leading_spaces

    out_py_file.write(leading_str)
    pos = leading_spaces if leading_str == '' else len(leading_str)
    first = True
    for data in array:
        segment = None
        if not first:
            segment = ', %s' % data
            if len(segment) + pos > max_width - 1:
                out_py_file.write(',\n')
                out_py_file.write(' ' * leading_spaces)
                pos = leading_spaces
                first = True
            else:
                pos += len(segment)
        if first:
            segment = data
            first = False
            pos += len(segment)
        assert segment is not None
        out_py_file.write(segment)
    if pos + len(trailing_str) < max_width - 1:
        out_py_file.write('%s\n' % trailing_str)
    else:
        out_py_file.write('\n')
        out_py_file.write(' ' * trailing_spaces)
        out_py_file.write(trailing_str)
        out_py_file.write('\n')


def parse_class_def(def_file: TextIO, out_py_file: TextIO, line_no: int):
    rollback_position = def_file.tell()
    line = def_file.readline()
    match = TOKEN.match(line)
    assert match, 'line %d: %s' % (line_no, line)
    class_name = match.group()
    out_py_file.write('\n\n# (L%d): %s\n' % (line_no, class_name))
    out_py_file.write('# noinspection DuplicatedCode,PyShadowingBuiltins,PyPep8Naming\n')
    out_py_file.write('class %s(SaveObject):\n' % class_name)
    rollback_position += len(class_name)
    def_file.seek(rollback_position)
    tmp_comments = StringIO()
    line_no = parse_new_line(def_file, tmp_comments, line_no)
    assert def_file.read(1) == '{', 'line %d: %s' % (line_no, line)
    line_no = parse_new_line(def_file, tmp_comments, line_no)
    for line in tmp_comments.getvalue().split('\n'):
        if line.strip() == '':
            continue
        out_py_file.write('    %s\n' % line)
    class_attrs = {}  # type: Dict[str, Dict[str, Any]]
    line_no = parse_class_body(def_file, class_attrs, line_no)
    assert def_file.read(1) == '}', 'line %d: %s' % (line_no, line)
    try:
        tmp_content = StringIO()
        line_no = parse_new_line(def_file, tmp_content, line_no)
        tmp_content = tmp_content.getvalue()
    except EOFError:
        tmp_content = ''

    # export fields
    slot_items = []
    for name, meta in class_attrs.items():
        if meta['type'] == 'comment':
            for line in meta['comment'].split('\n'):
                if line != '':
                    out_py_file.write('    %s\n' % line)
            continue
        name = camel_to_underline(name)
        if meta['type'] in BUILTIN_TYPES:
            py_type = meta['type']
        else:
            py_type = "'%s'" % meta['type']
        if meta['is_array']:
            py_type = 'List[%s]' % py_type
        # convert List[uint8] to bytes to improve performance
        if py_type == 'List[uint8]':
            py_type = 'bytes'
        comment = meta['comment']
        if meta['if_clause']:
            py_type = 'Optional[%s]' % py_type
            extra_comment = 'if (%s)' % meta['if_clause']
            if comment is None:
                comment = extra_comment
            else:
                comment = '%s; %s' % (extra_comment, comment)
        if meta['assertion']:
            extra_comment = '= %s' % repr(meta['assertion']['value'])
            if comment is None:
                comment = extra_comment
            else:
                comment = '%s; %s' % (extra_comment, comment)
        slot_items.append(name)
        out_py_file.write('    %s: %s' % (name, py_type))
        if comment is not None and comment != '':
            out_py_file.write('  # %s' % comment)
        out_py_file.write('\n')

        meta['generated_comment'] = comment
        meta['generated_type'] = py_type
        meta['generated_name'] = name

    # generate __slots__
    out_py_file.write('\n')
    pretty_write(out_py_file, ["'%s'" % x for x in slot_items], leading_str='    __slots__ = [', trailing_str=']')

    # generate __init__
    out_py_file.write('\n')
    init_params = ['%s: %s' % (meta['generated_name'], meta['generated_type']) for _, meta in class_attrs.items()
                   if meta['type'] != 'comment']
    # add "location_start" and "location_end" of SaveObject class
    init_params.append('location_start: int = -1')
    init_params.append('location_end: int = -1')
    pretty_write(out_py_file, init_params, leading_str='    def __init__(self, ', leading_spaces=17, trailing_str='):')
    for meta in class_attrs.values():
        if meta['type'] == 'comment':
            continue
        out_py_file.write('        self.%s = %s\n' % (meta['generated_name'], meta['generated_name']))
    out_py_file.write('        self.location_start = location_start\n')
    out_py_file.write('        self.location_end = location_end\n')

    # generate parse method
    out_py_file.write('\n')
    out_py_file.write('    # noinspection PyUnusedLocal\n')
    out_py_file.write('    @classmethod\n')
    out_py_file.write('    def parse(cls, stream: BinaryIO, props: tuple = ()):\n')
    out_py_file.write('        location_start = stream.tell()\n')
    for meta in class_attrs.values():
        if meta['type'] == 'comment':
            continue
        if meta['props']:
            props = [camel_to_underline(x) for x in meta['props']]
            if len(props) > 1:
                props_str = ', (%s)' % ', '.join(props)
            else:
                props_str = ', (%s,)' % props[0]
        else:
            props_str = ''
        if meta['injected']:
            assign_stmt = 'props[%d]' % meta['assertion']['value']
        else:
            assign_stmt = '%s.parse(stream%s)' % (meta['type'], props_str)
        if meta['is_array']:
            assign_stmt = '[%s for i in range(%s)]' % (assign_stmt, camel_to_underline(meta['array_size']))
            # special case for List[uint8]
            if meta['generated_type'] == 'bytes':
                assign_stmt = 'bytes(stream.read(%s))' % camel_to_underline(meta['array_size'])
        if meta['if_clause']:
            out_py_file.write('        if %s:\n' % camel_to_underline(meta['if_clause']))
            out_py_file.write('            %s = %s\n' % (meta['generated_name'], assign_stmt))
            out_py_file.write('        else:\n')
            if meta['default']:
                if meta['default']['type'] == 'ref':
                    out_py_file.write('            %s = %s\n' % (meta['generated_name'],
                                                                 camel_to_underline(meta['default']['value'])))
                else:  # constant
                    out_py_file.write('            %s = %s\n' % (meta['generated_name'],
                                                                 repr(meta['default']['value'])))
            else:
                # no default value
                out_py_file.write('            %s = None\n' % meta['generated_name'])
        else:
            out_py_file.write('        %s = %s\n' % (meta['generated_name'], assign_stmt))
        if meta['assertion'] and not meta['injected']:
            if meta['assertion']['type'] == 'ref':
                out_py_file.write('        assert %s == %s\n' % (meta['generated_name'],
                                                                 camel_to_underline(meta['assertion']['value'])))
            else:
                if type(meta['assertion']) == str:
                    out_py_file.write('        assert %s == %s\n' % (meta['generated_name'],
                                                                     repr(bytes(meta['assertion']['value'], 'utf8'))))
                elif type(meta['assertion']) == float:
                    out_py_file.write('        assert abs(%s - %s) < %s\n' % (meta['generated_name'],
                                                                              repr(meta['assertion']['value']),
                                                                              repr(FLOAT_COMPARISON_EPS)))
                else:
                    out_py_file.write('        assert %s == %s\n' % (meta['generated_name'],
                                                                     repr(meta['assertion']['value'])))

    out_py_file.write('        location_end = stream.tell()\n')
    # add "location_start" and "location_end"
    slot_items.extend(['location_start', 'location_end'])
    pretty_write(out_py_file, slot_items, leading_str='        return cls(', trailing_str=')')

    if tmp_content != '':
        out_py_file.write('\n')
        out_py_file.write(tmp_content)
    return line_no


def parse_new_line(def_file: TextIO, out_py_file: TextIO, line_no: int):
    while True:
        rollback_position = def_file.tell()
        line = def_file.readline()
        # skip empty line
        if len(line) == 0:
            raise EOFError()
        # skip space
        match = SPACES.match(line)
        if match:
            line = line[match.end():]
            rollback_position += match.end()
        if len(line) == 0 or line == '\n':
            line_no += 1
            rollback_position += len(line)
            continue
        def_file.seek(rollback_position)
        if line.startswith('//'):
            line_no = parse_comment(def_file, out_py_file, line_no)
        else:
            return line_no


def parse_def_document(def_file: TextIO, out_py_file: TextIO, line_no: int = 1):
    while True:
        line_no = parse_new_line(def_file, out_py_file, line_no)
        line_no = parse_class_def(def_file, out_py_file, line_no)


def compute_sha256(file: str):
    with open(file, 'rb') as f:
        sha256 = hashlib.sha256()
        while True:
            data = f.read(1024 * 1024)
            if not data:
                break
            sha256.update(data)
        return sha256.hexdigest()


# get the last non-empty line of a file
def last_line_of_file(file: str):
    with open(file, 'r') as f:
        last_non_empty_line = ''
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            last_non_empty_line = line
        return last_non_empty_line


def generate_parser(def_file: str, out_py_file: str):
    def_file_sha256 = compute_sha256(def_file)
    if os.path.isfile(out_py_file):
        last_line = last_line_of_file(out_py_file)
        if last_line.startswith('# sha256: '):
            sha256 = last_line[10:]
            if sha256 == def_file_sha256:
                return
    with open(out_py_file, 'w', encoding='utf8') as f:
        f.write('# Auto-generated file, do not edit\n\n')
        f.write('from .common import *\nfrom typing import *\nfrom typing import BinaryIO\n\n')
        with open(def_file, 'r', encoding='utf8') as f_def_fs:
            with StringIO(f_def_fs.read()) as f_def:
                try:
                    parse_def_document(f_def, f)
                except EOFError:
                    pass
                f.write('\n# generated at: %s\n' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                f.write('# sha256: %s\n' % def_file_sha256)
