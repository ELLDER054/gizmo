from myparser import Parser
from lexer import Lexer
from error import Errors
error = Errors()

if __name__ == '__main__':
    with open('main.gizmo') as f:
        code = f.read() or 'int add(int x, int y) {\n\treturn x + y;\n}\nwrite(add(14567, 87906));'

    try:
        lexer = Lexer()
        tokens = lexer.lex(code)

        parser = Parser()

        tree = parser.parse(tokens)
        for i, statement in enumerate(tree):
            if statement is not None:
                s = statement.toStr()
                print(s)
    except Exception as e:
       print(e)
