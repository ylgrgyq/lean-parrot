"""
    Functions to parse input from command line
"""
import json

def skip_whitespaces(pos, a_str):
    while pos < len(a_str) and a_str[pos].isspace():
        pos += 1
    return pos

def parse_keyword_from_input(pos, input_str):
    cursor = pos
    while cursor < len(input_str):
        char = input_str[cursor]
        if char.isalpha():
            cursor += 1
        elif char.isspace():
            key = input_str[pos:cursor]
            cursor = skip_whitespaces(cursor, input_str)
            return [cursor, key]
        else:
            raise RuntimeError("Invalid keyword in input %s" % input_str)

def parse_json(pos, input_str):
    brackets_count = 1
    cursor = pos + 1
    while cursor < len(input_str):
        if input_str[cursor] == '{':
            brackets_count += 1
        elif input_str[cursor] == '}':
            brackets_count -= 1
            if brackets_count == 0:
                cursor = skip_whitespaces(cursor + 1, input_str)
                json_str = input_str[pos:cursor].replace('\'', '\"')
                return [cursor, json.loads(json_str)]
        cursor += 1

    raise RuntimeError("Invalid JSON string in input: %s" % input_str)

def parse_list(pos, input_str):
    ret = list()
    cursor = pos + 1
    while cursor < len(input_str):
        if input_str[cursor] == ']':
            cursor = skip_whitespaces(cursor + 1, input_str)
            return [cursor, ret]
        else:
            [cursor, value] = parse_value_from_input(cursor, input_str)
            ret.append(value)

    raise RuntimeError("Missing ']' in list. input: %s" % input_str)

def parse_string(pos, input_str):
    quote_char = input_str[pos]
    cursor = pos + 1
    while cursor < len(input_str) and input_str[cursor] != quote_char:
        cursor += 1

    ret_str = input_str[pos + 1:cursor]
    if cursor < len(input_str):
        cursor = skip_whitespaces(cursor + 1, input_str)
    return [cursor, ret_str]

def parse_value_from_input(pos, input_str):
    cursor = pos
    if input_str[cursor] == '{':
        return parse_json(cursor, input_str)
    elif input_str[cursor] == '[':
        return parse_list(cursor, input_str)
    elif input_str[cursor] in ['\'', '\"']:
        return parse_string(cursor, input_str)
    else:
        while cursor < len(input_str) \
              and not input_str[cursor].isspace() \
              and input_str[cursor] not in ['}', ']']:
            cursor += 1
        return [skip_whitespaces(cursor, input_str), input_str[pos:cursor]]

def parse_input_cmd_args(input_str):
    ret = dict()
    pos = skip_whitespaces(0, input_str)
    while pos < len(input_str):
        [nxt_pos, key] = parse_keyword_from_input(pos, input_str)
        [nxt_pos, value] = parse_value_from_input(nxt_pos, input_str)
        pos = nxt_pos
        ret[key] = value
    return ret
