from error import Errors
error = Errors()


class Token(object):
    def __init__(self, typ, val, line):
        self.typ = typ
        self.val = val
        self.lineno = line


class Lexer(object):
    def __init__(self):
        self.lineno = 1

    def lex_num(self, line):
        num = ""
        can_find_dot = True
        for c in line:
            if c == '.' and can_find_dot is not False:
                can_find_dot = False
                num += c
                continue
            elif c == '.' and can_find_dot is False:
                error.throwSyntax(self.lineno, 'Multiple dots in floating point number')
                break
            if not c.isdigit() and c != '.':
                break
            num += c
        if can_find_dot is False:
            return 'REAL', float(num), len(num)
        return 'INT', int(num), len(num)

    def lex_string(self, line):
        delimiter = line[0]
        found_delimiter = False
        string = ""
        for c in line[1:]:
            if c == delimiter:
                found_delimiter = True
                break
            string += c
        if found_delimiter:
            return '"'+string+'"', len(string)+2
        else:
            error.throwSyntax(self.lineno, 'Unexpected end of input')
            return None, len(string)+1

    def lex_id(self, line):
        keys = ('Class', 'PI', 'return')
        id = ""
        types = ('int', 'string', 'bool', 'real', 'list', 'none')
        builtins = ('write', 'eval', 'read')
        for c in line:
            if not c.isdigit() and not c.isalpha() and c != '_':
                break
            id += c
        if id in keys:
            return 'KEY', id, len(id)
        elif id in types:
            return 'TYPE', id, len(id)
        elif id in builtins:
            return 'BUILT', id, len(id)
        else:
            return 'ID', id, len(id)

    def lex_comment(self, line):
        consumed = 0
        for c in line:
            if c == '\n':
                consumed += 1
                break
            consumed += 1
        return consumed

    def lex_multi_comment(self, line):
        consumed = 0
        for i, c in enumerate(line):
            if c == '\\' and line[i+1] == ')':
                return consumed+2
            consumed += 1
        return consumed

    def lex(self, line):
        tokens = []
        literals = {'(': 'LP', ')': 'RP', '{': 'LCB', '}': 'RCB', '[': 'LSB', ']': 'RSB', '.': 'DOT', ',': 'CMA', ':': 'COLON', ';': 'SCOLON'}
        operators = ('/', '*', '+', '-', '%')
        lexeme_count = 0
        while lexeme_count < len(line):
            lexeme = line[lexeme_count]
            if lexeme.isdigit():
                typ, tok, consumed = self.lex_num(line[lexeme_count:])
                tokens.append(Token(typ, tok, self.lineno))
                lexeme_count += consumed
            elif lexeme == '"' or lexeme == "'":
                tok, consumed = self.lex_string(line[lexeme_count:])
                if tok is not None:
                    tokens.append(Token('STR', tok, self.lineno))
                lexeme_count += consumed
            elif lexeme.isalpha() or lexeme == '_':
                typ, tok, consumed = self.lex_id(line[lexeme_count:])
                tokens.append(Token(typ, tok, self.lineno))
                lexeme_count += consumed
            elif lexeme in operators:
                tokens.append(Token(lexeme, lexeme, self.lineno))
                lexeme_count += 1
            elif lexeme == '=':
                if line[lexeme_count+1] == '=':
                    tokens.append(Token('EQ', '==', self.lineno))
                    lexeme_count += 2
                else:
                    tokens.append(Token('ASSIGN', '=', self.lineno))
                    lexeme_count += 1
            elif lexeme == '\n':
                self.lineno += 1
                lexeme_count += 1
            elif lexeme == '<':
                if line[lexeme_count+1] == '=':
                    tokens.append(Token('LE', '<=', self.lineno))
                    lexeme_count += 2
                else:
                    tokens.append(Token('LT', '<', self.lineno))
                    lexeme_count += 1
            elif lexeme == '>':
                if line[lexeme_count+1] == '=':
                    tokens.append(Token('GE', '>=', self.lineno))
                    lexeme_count += 2
                else:
                    tokens.append(Token('GT', '>', self.lineno))
                    lexeme_count += 1
            elif lexeme == '!':
                if line[lexeme_count+1] == '=':
                    tokens.append(Token('NE', '!=', self.lineno))
                    lexeme_count += 2
            elif lexeme in literals:
                tokens.append(Token(literals[lexeme], lexeme, self.lineno))
                lexeme_count += 1
            elif lexeme == " " or lexeme == '\t':
                lexeme_count += 1
            elif lexeme == "\\":
                if line[lexeme_count+1] == "(":
                    consumed = self.lex_multi_comment(line[lexeme_count+2:])
                    lexeme_count += consumed
                else:
                    consumed = self.lex_comment(line[lexeme_count:])
                    lexeme_count += consumed
            else:
                error.throwSyntax('Unexpected character `%s\'' % lexeme)
                lexeme_count += 1
        return tokens
