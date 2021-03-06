import os
import re
from typing import Optional, List, Dict, Pattern, Match, NamedTuple, Union
from types import ModuleType

__all__ = [
    'wrap_header',
]

# ---------------------------------------------------------
# region CONSTANTS & ENUMS

LOADER_SRC = '''# -*- encoding: utf-8 -*-

# ============================================================================ #
#                                   WARNING                                    #
# ---------------------------------------------------------------------------- #
#                           DO NOT MODIFY THIS FILE                            #
#                                                                              #
#                   This file is generated by source code.                     #
#                   Changes in the source will not persist.                    #
# ============================================================================ #


import sys
import os
import platform
import ctypes
from enum import IntEnum, auto
from ctypes import (
    c_bool,
    c_char_p,
    c_char,
    c_byte,
    c_ubyte,
    c_int,
    c_uint,
    c_short,
    c_ushort,
    c_long,
    c_ulong,
    c_void_p,
    # c_ssize_t,
    # c_size_t,
    c_float,
    c_double,
    CFUNCTYPE,
    POINTER,
    CDLL,
    WinDLL,
    Structure,
    byref,
)

# region LIBRARY LOADER

_lib_fname = {
    'win32': 'raylib.dll',
    'linux': 'libraylib.so.2.5.0',
    'darwin': 'libraylib.2.5.0.dylib'
}

_lib_platform = sys.platform

if _lib_platform == 'win32':
    _bitness = platform.architecture()[0]
else:
    _bitness = '64bit' if sys.maxsize > 2 ** 32 else '32bit'

_lib_fname_abspath = os.path.join(os.path.dirname(os.path.abspath(__file__)), _lib_fname[_lib_platform])
_lib_fname_abspath = os.path.normcase(os.path.normpath(_lib_fname_abspath))

print(
    """Library loading info:
    platform: {}
    arch: {}
    absolute path: {}
    exists: {}
    is file: {}
    """.format(
        _lib_platform,
        _bitness,
        _lib_fname_abspath,
        'yes' if os.path.exists(_lib_fname_abspath) else 'no',
        'yes' if os.path.isfile(_lib_fname_abspath) else 'no'
    )
)

_rl = None
if _lib_platform == 'win32':
    from ctypes import wintypes

    DONT_RESOLVE_DLL_REFERENCES = 0x00000001
    LOAD_LIBRARY_AS_DATAFILE = 0x00000002
    LOAD_WITH_ALTERED_SEARCH_PATH = 0x00000008
    LOAD_IGNORE_CODE_AUTHZ_LEVEL = 0x00000010  # NT 6.1
    LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x00000020  # NT 6.0
    LOAD_LIBRARY_AS_DATAFILE_EXCLUSIVE = 0x00000040  # NT 6.0
    
    # These cannot be combined with LOAD_WITH_ALTERED_SEARCH_PATH.
    # Install update KB2533623 for NT 6.0 & 6.1.
    LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR = 0x00000100
    LOAD_LIBRARY_SEARCH_APPLICATION_DIR = 0x00000200
    LOAD_LIBRARY_SEARCH_USER_DIRS = 0x00000400
    LOAD_LIBRARY_SEARCH_SYSTEM32 = 0x00000800
    LOAD_LIBRARY_SEARCH_DEFAULT_DIRS = 0x00001000

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    def check_bool(result, func, args):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
        return args

    kernel32.LoadLibraryExW.errcheck = check_bool
    kernel32.LoadLibraryExW.restype = wintypes.HMODULE
    kernel32.LoadLibraryExW.argtypes = (wintypes.LPCWSTR,
                                        wintypes.HANDLE,
                                        wintypes.DWORD)


    class CDLLEx(ctypes.CDLL):
        def __init__(self, name, mode=0, handle=None,
                     use_errno=True, use_last_error=False):
            if handle is None:
                handle = kernel32.LoadLibraryExW(name, None, mode)
            super(CDLLEx, self).__init__(name, mode, handle,
                                         use_errno, use_last_error)


    class WinDLLEx(WinDLL):
        def __init__(self, name, mode=0, handle=None,
                     use_errno=False, use_last_error=True):
            if handle is None:
                handle = kernel32.LoadLibraryExW(name, None, mode)
            super(WinDLLEx, self).__init__(name, mode, handle,
                                           use_errno, use_last_error)


    try:
        _rl = CDLLEx(_lib_fname_abspath, LOAD_WITH_ALTERED_SEARCH_PATH)
    except OSError:
        print("Unable to load raylib 2.5.0 dll.")
        _rl = None
else:
    _rl = CDLL(_lib_fname_abspath)

if _rl is None:
    print("Failed to load shared library.")
    exit()

# endregion (library loader)
'''.split('\n')


class Regex(NamedTuple):
    name: str
    rule: Pattern

    def __call__(self, string: str) -> Optional[Match]:
        return self.rule.match(string)

    def replace(self, old_string: str):
        while True:
            m: Match = self.rule.search(old_string)
            if m:
                old_string = old_string.replace(m[0], m[1])
            else:
                break
        return old_string


RULE_DEFINE = Regex("DEFINE", re.compile(r"\s*#define\s+(\w+)\s+([a-zA-Z0-9./()]+)(\s+.*)?"))
RULE_REALNUM_SUFFIX = Regex("DEFINE", re.compile(r"(\d+)[fd]"))
RULE_COLOR_DEFINES = Regex("COLOR_DEFINES",
                           re.compile(r"#define\s+(\w+)\s+CLITERAL\(Color\){ (\d+, \d+, \d+, \d+) \}(\s+.*)"))
RULE_STRUCT_EMPTY = Regex("STRUCT_EMPTY", re.compile(r"typedef struct (\w+) (\w+);"))
RULE_STRUCT_MEMBER = Regex("STRUCT_MEMBER", re.compile(r"\s+((unsigned)? \w+ \**)(\w+(\[\d+])?(, \w+(\[\d+])?)*);"))
RULE_STRUCT_MEMBER_ARRAY = Regex("STRUCT_MEMBER_ARRAY", re.compile(r"(\w+)\[(\d+)\]"))
RULE_STRUCT_BEGIN = Regex("STRUCT_BEGIN", re.compile(r"typedef struct (\w+) {"))
RULE_STRUCT_END = Regex("STRUCT_END", re.compile(r"} (\w+);"))
RULE_TYPE_ALIAS_DEFINE = Regex("TYPE_ALIAS_DEFINE", re.compile(r"\s*#define\s+(\w+)\s+(\w+)\s+(// .*)"))
RULE_TYPE_ALIAS_TYPEDEF = Regex("TYPE_ALIAS_TYPEDEF", re.compile(r"\s*typedef\s+(\w+)\s+(\w+);(\s+// .*)?"))
RULE_ENUM_BEGIN = Regex("ENUM_BEGIN", re.compile(r"typedef enum {"))
RULE_ENUM_MEMBER = Regex("ENUM_MEMBER", re.compile(r"\s+(\w+),?(\s+.*)?"))
RULE_ENUM_MEMBER_VALUE = Regex("ENUM_MEMBER", re.compile(r"\s+(\w+)\s+= (\d+),?(\s+.*)?"))
RULE_ENUM_END = Regex("ENUM_END", re.compile(r"} (\w+);"))
RULE_NAME_ALIAS = Regex("NAME_ALIAS", re.compile(r"#define (\w+)\s+(\w+)"))
RULE_CALLBACK_NOTATION = Regex("CALLBACK_NOTATION", re.compile(r"typedef (\w+)\s+\(\*(\w+)\)(.*);"))
RULE_FUNCTION = Regex("FUNCTION", re.compile(r"RLAPI (const )?(unsigned )?(\w+) (\**)(\w+)(.*);"))
RULE_PARAM = Regex("PARAM", re.compile(r"(const )?(unsigned )?(\w+) (\**)(\w+)"))

RULE_PROCESS = re.compile(r"// @(\w+)( \d+)?")
RULE_COMMENT = re.compile(r"// (.*)")

C_TYPES = {
    'void',
    'bool',
    'char',
    'byte',
    'short',
    'int',
    'long',
    'longlong',
    'float',
    'double',
    'longdouble',
}

C_TO_PY_TYPES = {
    'c_void_p': 'int',
    'c_bool': 'bool',
    'c_char': 'bytes',
    'c_char_p': 'bytes',
    'c_byte': 'int',
    'c_ubyte': 'int',
    'c_short': 'int',
    'c_ushort': 'int',
    'c_int': 'int',
    'c_uint': 'int',
    'c_long': 'int',
    'c_ulong': 'int',
    'c_longlong': 'int',
    'c_ulonglong': 'int',
    'c_float': 'float',
    'c_double': 'float',
    'c_longdouble': 'float',
}

PROCESS_LINES = [
    'define_begin',
    'define_end',
    'define_skip',
    'color_defines_begin',
    'color_defines_end',
    'struct_begin',
    'struct_end',
    'type_alias_define',
    'type_alias_typedef',
    'enum_begin',
    'enum_end',
    'define_name_alias',
    'callback_notation',
    'functions_begin',
    'functions_end',
]


# endregion (constants)
# ---------------------------------------------------------
# region FUNCTIONS

def load_source(location: str) -> List[str]:
    with open(location, 'r') as src:
        return src.readlines()


def to_snake_case(camel_case: str) -> str:
    """Converts a camel case name to a snake case and returns it."""
    snake_case: str = ''
    last: bool = True
    for i, ch in enumerate(camel_case):
        if ch.isupper():
            if not last:
                snake_case += '_'
            last = True
        else:
            last = False
        snake_case += ch.lower()

    return snake_case


def typename(unsigned: bool, dtype: str, ptr_level: int, array_len: int) -> str:
    lv: int = ptr_level
    dtype = dtype.strip(' ')
    if dtype in C_TYPES:
        if unsigned and dtype == 'char':
            dtype = 'byte'
        if unsigned:
            dtype = 'u' + dtype
        if dtype in ('char', 'void') and lv > 0:
            dtype += '_p'
            lv -= 1
        dtype = 'c_' + dtype
    elif dtype == 'va_list':
        dtype = 'c_void_p'

    if array_len > 0:
        dtype = f"{dtype} * {array_len}"

    while lv > 0:
        dtype = f"POINTER({dtype})"
        lv -= 1

    if dtype == 'c_void':
        dtype = 'None'

    return dtype


def wrap_header(path_to_header: Optional[str] = None, path_to_output: Optional[str] = None,
                import_module: bool=False) -> Union[str, ModuleType]:
    if path_to_header is None:
        path_to_header = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raylib.h")
    if path_to_output is None:
        path_to_output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raylib.py")

    lines: List[str] = load_source(path_to_header)
    active_rules: List[Regex] = []
    exported_names: List[str] = ["__all__ = ["]
    generated_code: List[str] = []
    funcion_wrappers: List[str] = []
    palette: List[str] = []
    callback_counter: int = 0
    define_alias_counter: int = 0
    last_comment: str = ""

    with open(path_to_output, 'w') as output:
        for lineno, line in enumerate(lines):
            comment: Match = re.match(RULE_COMMENT, line)
            if comment:
                last_comment = comment[1]
                m: Match = re.match(RULE_PROCESS, line)
                if m:
                    last_comment = ""
                    command: str = m[1]
                    # print(lineno + 1, command)
                    if command == 'define_begin':
                        active_rules.append(RULE_DEFINE)
                    elif command == 'define_end':
                        active_rules.remove(RULE_DEFINE)
                        generated_code.append("")
                    elif command == 'functions_begin':
                        active_rules.append(RULE_FUNCTION)
                    elif command == 'functions_end':
                        active_rules.remove(RULE_FUNCTION)
                    elif command == 'struct_begin':
                        active_rules.append(RULE_STRUCT_BEGIN)
                        active_rules.append(RULE_STRUCT_EMPTY)
                        active_rules.append(RULE_STRUCT_MEMBER)
                        active_rules.append(RULE_STRUCT_END)
                        active_rules.append(RULE_TYPE_ALIAS_TYPEDEF)
                        active_rules.append(RULE_TYPE_ALIAS_DEFINE)
                    elif command == 'struct_end':
                        active_rules.remove(RULE_STRUCT_BEGIN)
                        active_rules.remove(RULE_STRUCT_EMPTY)
                        active_rules.remove(RULE_STRUCT_MEMBER)
                        active_rules.remove(RULE_STRUCT_END)
                        active_rules.remove(RULE_TYPE_ALIAS_TYPEDEF)
                        active_rules.remove(RULE_TYPE_ALIAS_DEFINE)
                    elif command == 'enum_begin':
                        active_rules.append(RULE_ENUM_BEGIN)
                        active_rules.append(RULE_ENUM_MEMBER)
                        active_rules.append(RULE_ENUM_MEMBER_VALUE)
                        active_rules.append(RULE_ENUM_END)
                    elif command == 'enum_end':
                        active_rules.remove(RULE_ENUM_BEGIN)
                        active_rules.remove(RULE_ENUM_MEMBER)
                        active_rules.remove(RULE_ENUM_MEMBER_VALUE)
                        active_rules.remove(RULE_ENUM_END)
                    elif command == 'callback_notation':
                         callback_counter = int(m[2], 10)
                         active_rules.append(RULE_CALLBACK_NOTATION)
                    elif command == 'color_defines_begin':
                        active_rules.append(RULE_COLOR_DEFINES)
                    elif command == 'color_defines_end':
                        active_rules.remove(RULE_COLOR_DEFINES)
                    elif command == 'define_name_alias':
                        define_alias_counter = int(m[2], 10)
                        active_rules.append(RULE_NAME_ALIAS)
            else:
                for rule in active_rules:
                    match: Match = rule(line)
                    if match:
                        # print(f"{rule.name} ({lineno + 1}): {line[:-1]}", file=output)
                        if rule is RULE_NAME_ALIAS:
                            generated_code.append(f"{match[1]} = {match[2]}")
                            exported_names.append(f"    '{match[1]}',")
                            define_alias_counter -= 1
                            if define_alias_counter <= 0:
                                active_rules.remove(RULE_NAME_ALIAS)
                                generated_code.append("")
                        if rule is RULE_TYPE_ALIAS_TYPEDEF:
                            generated_code.append(f"\n{match[2]} = {match[1]}\n")
                            exported_names.append(f"    '{match[2]}',")
                        if rule is RULE_TYPE_ALIAS_DEFINE:
                            generated_code.append(f"\n{match[1]} = {match[2]}\n")
                            exported_names.append(f"    '{match[1]}',")
                        if rule is RULE_STRUCT_EMPTY:
                            generated_code.append(f"\nclass {match[1]}(Structure):\n    pass\n")
                            exported_names.append(f"    '{match[1]}',")
                        elif rule is RULE_DEFINE:
                            value: str = match[2]
                            value = RULE_REALNUM_SUFFIX.replace(value)
                            generated_code.append(f"{match[1]} = {value}")
                            exported_names.append(f"    '{match[1]}',")
                        elif rule is RULE_ENUM_BEGIN:
                            EnumData.begin(last_comment)
                        elif rule is RULE_ENUM_MEMBER:
                            EnumData.current.add_member(match[1], 'auto()')
                        elif rule is RULE_ENUM_MEMBER_VALUE:
                            EnumData.current.add_member(match[1], match[2])
                        elif rule is RULE_ENUM_END:
                            EnumData.current.name = match[1]
                            EnumData.end(generated_code, exported_names)

                        elif rule is RULE_COLOR_DEFINES:
                            color_comment = match[3].replace("//", '#')
                            palette.append(f"{match[1]} = Color({match[2]}) {color_comment}")

                        elif rule is RULE_STRUCT_BEGIN:
                            StructData.begin(last_comment)
                            StructData.current.name = match[1]
                        elif rule is RULE_STRUCT_EMPTY:
                            print('#')
                        elif rule is RULE_STRUCT_MEMBER:
                            # print(lineno + 1, match.groups())
                            name: str = match[3]
                            arraymatch: Match = RULE_STRUCT_MEMBER_ARRAY(name)
                            array_len: Optional[str] = None
                            if arraymatch:
                                name = arraymatch[1]
                                array_len = arraymatch[2]
                            StructData.current.add_field(name, match[1], array_len)
                        elif rule is RULE_STRUCT_END:
                            StructData.end(generated_code, exported_names)

                        elif rule is RULE_CALLBACK_NOTATION:
                            cb_name: str = match[2]
                            cb_type: typename(False, match[1], 0, -1)
                            cb_params: List[str] = match[3].strip('()').split(', ')
                            cb_ptypes: List[str] = []
                            for param in cb_params:
                                parammatch: Match = RULE_PARAM(param)
                                if parammatch:
                                    cb_ptypes.append(typename(
                                        parammatch[2] is not None,
                                        parammatch[3],
                                        len(parammatch[4]),
                                        -1
                                    ))
                            callback: str = f"{cb_name} = CFUNCTYPE({', '.join(cb_ptypes)})"
                            generated_code.append("")
                            generated_code.append(callback)
                            generated_code.append("")
                            exported_names.append(f"    '{cb_name}',")
                            print(callback)
                            callback_counter -= 1
                            if callback_counter <= 0:
                                active_rules.remove(RULE_CALLBACK_NOTATION)

                        elif rule is RULE_FUNCTION:
                            func: FunctionData = FunctionData()
                            func.unsigned = match[2] is not None
                            func.rettype = match[3]
                            func.ptr_level = len(match[4])
                            func.name = match[5]
                            params: str = match[6]
                            if params != '(void)':
                                if ',' in params:
                                    paramlist: List[str] = params.strip('()').split(', ')
                                else:
                                    paramlist: List[str] = [params.strip('()')]
                                for param in paramlist:
                                    if param == '...':
                                        func.add_param(False, '', 0, '', True)
                                    else:
                                        parammatch: Match = RULE_PARAM(param)
                                        if parammatch:
                                            func.add_param(
                                                parammatch[2] is not None,
                                                parammatch[3],
                                                len(parammatch[4]),
                                                parammatch[5],
                                                False
                                            )
                            func.convert(funcion_wrappers, exported_names)

        exported_names.append(']\n')
        for line in (LOADER_SRC + exported_names + generated_code + palette + funcion_wrappers):
            print(line, file=output)

    if import_module:
        modname: str = os.path.basename(path_to_output)[:-3]
        exec(f"import {modname}")
        return globals()[modname]
    else:
        return path_to_output

# endregion (functions)
# ---------------------------------------------------------
# region CLASSES


class EnumData:
    current: Optional['EnumData'] = None

    @classmethod
    def begin(cls, doc: str = ""):
        assert cls.current is None, "Overlapped Enumeration."
        cls.current = cls(doc)

    @classmethod
    def end(cls, lines: List[str], export: List[str]):
        if cls.current:
            cls.current.convert(lines, export)
            cls.current = None

    def __init__(self, doc: str = ""):
        self.doc: str = doc
        self.name: str = ""
        self.members: Dict[str, str] = {}
        self.prefix: str = ""
        self.correct: bool = False

    def add_member(self, name: str, value: str = 'auto()'):
        prefix, mname = name.split('_', 1)
        if mname[0].isdigit():
            self.correct = True
        if self.prefix == '':
            self.prefix = prefix
        self.members[mname] = value

    def convert(self, lines: List[str], export: List[str]):
        assert self.name != "", "Enum name is undefined."
        assert len(self.members), "Enum is empty."

        export.append(f"    '{self.name}',")
        lines.append("")
        lines.append(f"class {self.name}(IntEnum):")
        if self.doc != "":
            lines.append(f'    """{self.doc}"""')
        for n in self.members:
            v = self.members[n]
            if self.correct:
                lines.append(f"    {self.prefix[0]}{n} = {v}")
            else:
                lines.append(f"    {n} = {v}")
        lines.append("\n")
        for n in self.members:
            if self.correct:
                lines.append(f"{self.prefix}_{n} = {self.name}.{self.prefix[0]}{n}")
                export.append(f"    '{self.prefix}_{n}',")
            else:
                lines.append(f"{self.prefix}_{n} = {self.name}.{n}")
                export.append(f"    '{self.prefix}_{n}',")
        lines.append("")


class StructData:
    c_types: List[str] = [
        'c_bool',
        'c_char',
        'c_byte',
        'c_ubyte',
        'c_short',
        'c_ushort',
        'c_int',
        'c_uint',
        'c_long',
        'c_ulong',
        'c_size_t',
        'c_ssize_t',
        'c_float',
        'c_double',
        'c_longdouble',
        'c_char_p',
        'c_wchar_p',
        'c_void_p'
    ]

    current: Optional['StructData'] = None

    @classmethod
    def begin(cls, doc: str = ""):
        assert cls.current is None, "Overlapped Structure."
        cls.current = cls(doc)

    @classmethod
    def end(cls, lines: List[str], export: List[str]):
        if cls.current:
            cls.current.convert(lines, export)
            cls.current = None

    def __init__(self, doc: str = ""):
        self.doc: str = doc
        self.name: str = ""
        self.fields: List[StructFieldData] = []

    def add_field(self, name: str, ftype: str, array_len: Optional[str] = None):
        if ',' in name:
            names = name.split(', ')
        else:
            names = [name]

        for n in names:
            field: StructFieldData = StructFieldData()
            field.ptr_level = ftype.count('*')
            field.unsigned = 'unsigned' in ftype
            field.name = n
            field.type = ftype.strip('*').strip(' ').replace('unsigned', '')
            if array_len:
                field.array_len = int(array_len, 10)
            self.fields.append(field)

    def convert(self, lines: List[str], exports: List[str]):
        lines.append("")
        lines.append(f"class {self.name}(Structure):")
        if self.doc != "":
            lines.append(f'    """{self.doc}"""')
        lines.append(f"    _fields_ = [")
        for field in self.fields:
            field.convert(lines)
        lines.append(f"    ]")
        lines.append("")
        exports.append(f"    '{self.name}',")


class StructFieldData:

    def __init__(self):
        self.name: str = ''
        self.type: str = ''
        self.unsigned: bool = False
        self.ptr_level: int = 0
        self.array_len: int = -1

    def convert(self, lines: List[str]):
        dtype: str = typename(self.unsigned, self.type, self.ptr_level, self.array_len)
        lines.append(f"       ('{self.name}', {dtype}),")


class FunctionData:

    def __init__(self):
        self.name: str = ''
        self.rettype: str = ''
        self.ptr_level: int = 0
        self.unsigned: bool = False
        self.params: List[FunctionParamData] = []

    def add_param(self, unsigned: bool, ptype: str, ptr_level: int, name: str, is_varargs: bool = False):
        param: FunctionParamData = FunctionParamData()
        if is_varargs:
            param.is_varargs = True
        else:
            param.unsigned = unsigned
            param.type = ptype
            param.ptr_level = ptr_level
            param.name = name
        self.params.append(param)

    def convert(self, lines: List[str], exports: List[str]):
        dtype: str = typename(self.unsigned, self.rettype, self.ptr_level, -1)
        pydtype: str = dtype
        if pydtype in C_TO_PY_TYPES:
            pydtype = C_TO_PY_TYPES[dtype]
        py_name: str = to_snake_case(self.name)
        params = ", ".join([p.convert_to_string() for p in self.params])
        ptypes = ", ".join([typename(p.unsigned, p.type, p.ptr_level, -1) for p in self.params if not p.is_varargs])
        pnames = ", ".join([p.py_name for p in self.params if not p.is_varargs])

        lines.append("")
        lines.append(f"_rl.{self.name}.argtypes = [{ptypes}]")
        lines.append(f"_rl.{self.name}.restype = {dtype}")
        lines.append(f"def {py_name}({params}) -> {pydtype}:")
        lines.append(f"    {'' if pydtype is 'None' else 'return '}_rl.{self.name}({pnames})")
        lines.append("")
        exports.append(f"    '{py_name}',")


class FunctionParamData:

    def __init__(self):
        self.name: str = ''
        self.type: str = ''
        self.ptr_level: int = 0
        self.unsigned: bool = False
        self.is_varargs: bool = False

    @property
    def py_name(self) -> str:
        return to_snake_case(self.name) if not self.is_varargs else "*args"

    def convert_to_string(self) -> str:
        if self.is_varargs:
            return "*args"

        dtype: str = typename(self.unsigned, self.type, self.ptr_level, -1)
        if dtype in C_TO_PY_TYPES:
            dtype = C_TO_PY_TYPES[dtype]
        py_name: str = to_snake_case(self.name)
        return f"{py_name}: {dtype}"


# endregion (classes)
# ---------------------------------------------------------
