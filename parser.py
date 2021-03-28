from error import Errors
from myast import *
error = Errors()

class SymbolTable:
    def __init__(self):
        self.table = []

    def set(self, name, typ, lenArgs=None):
        if lenArgs is None:
            self.table.append([name, typ])
        else:
            self.table.append([name, typ, lenArgs])

    def get(self, name, lineno, lenArgs=None):
        for sym in self.table:
            if sym[0] == name:
                if lenArgs is not None:
                    if sym[2] != lenArgs:
                        error.throwArgument(lineno, 'Wrong amount of arguments for function `%s\'. Gave %d, expected %d' % (name, lenArgs, sym[2]))
                return sym[1:]
        error.throwName(lineno, 'Undefined name `%s\'' % name)

    def pop(self, names):
        for i in range(len(names)):
            if i < len(self.table):
                self.table.pop(i)


class Parser(object):
    def __init__(self):
        self.index = 0
        self.symbolTable = SymbolTable()
        self.builtins = {'write': [WriteNode, 1], 'read': [ReadNode, 1], 'eval': [ExprNode, 1]}
        self.inFunction = False

    def eatTyp(self, typ):
        # make sure we are not out of range
        if not len(self.tokens) > self.index:
            return None
        # check if the next token type is what we expect
        if self.tokens[self.index].typ == typ:
            self.index += 1
            return self.tokens[self.index-1].val
        return None

    def eatVal(self, val):
        # make sure we are not out of range
        if not len(self.tokens) > self.index:
            return None
        # check if the next token value is what we expect
        if self.tokens[self.index].val == val:
            self.index += 1
            return self.tokens[self.index-1].typ
        return None

    def eatTok(self, tok):
        # make sure we are not out of range
        if not len(self.tokens) > self.index:
            return None
        # check if the next token is what we expect
        if self.tokens[self.index].typ == tok[0] and self.tokens[self.index].val == tok[1]:
            self.index += 1
            return self.tokens[self.index-1]
        return None

    # ID -> IDENTIFIER . ID | IDENTIFIER
    def identifier(self):
        pass

    # EXPR -> EXPR1 | TERM
    def expression(self, start):
        self.index = start
        return self.expression1(self.index) or self.term(start)

    # EXPR1 -> TERM [+-] EXPR
    def expression1(self, start):
        self.index = start
        term = self.term(self.index)
        if term is None:
            self.index = start
            return None
        tlineno = self.tokens[self.index-1].lineno
        oper = self.eatVal('+')
        if oper is None:
            oper = self.eatVal('-')
            if oper is None:
                self.index = start
                return None
        expr = self.expression(self.index)
        if expr is None:
            self.index = start
            return None
        if oper == '+':
            self.check_type(term, expr, tlineno, '+')
        else:
            self.check_type(term, expr, tlineno)
        node = OperatorNode(oper, term, expr)
        node.typ = self.typeof(term, tlineno)
        return node

    # TERM -> TERM1 | FACTOR
    def term(self, start):
        self.index = start
        return self.term1(self.index) or self.factor(start)

    # TERM1 -> FACTOR [*/] TERM
    def term1(self, start):
        self.index = start
        factor = self.factor(self.index)
        if factor is None:
            self.index = start
            return None
        flineno = self.tokens[self.index-1].lineno
        oper = self.eatVal('*')
        if oper is None:
            oper = self.eatVal('/')
            if oper is None:
                self.index = start
                return None
        term = self.term(self.index)
        if term is None:
            self.index = start
            error.throwExpected(self.tokens[self.index-1].lineno, 'right hand of expression')
            return None
        if oper == '/':
            if isinstance(term, IntegerNode) and term.val == 0:
                error.throwZeroDivision(self.tokens[self.index+1].lineno)
        self.check_type(factor, term, flineno)
        node = OperatorNode(oper, factor, term)
        node.typ = self.typeof(factor, flineno)
        return node

    # function for getting type of a node
    def typeof(self, node, lineno):
        types = {
            StringNode: 'string',
            IntegerNode: 'int',
            ListNode: 'list',
            RealNode: 'real',
            int: 'int',
            str: 'string',
        }
        if type(node) != IdentifierNode and type(node) != FuncCallNode and type(node) != OperatorNode:
            return types[type(node)]
        elif type(node) == FuncCallNode:
            return self.symbolTable.get(node.name, lineno)[0]
        elif type(node) == OperatorNode:
            return node.left.typ
        else:
            return self.symbolTable.get(node.val, lineno)[0]

    # function for checking types in an expression
    def check_type(self, left, right, lineno, operation=""):
        if operation == '+':
            # allow both string concatention and integer addition
            if self.typeof(left, lineno) == 'int':
                if self.typeof(right, lineno) != 'int':
                    error.throwType(lineno, 'Expected right hand side of expression(%s) to be same as left hand side(int)' % self.typeof(right, lineno))
            if self.typeof(left, lineno) == 'string':
                if self.typeof(right, lineno) != 'string':
                    error.throwType(lineno, 'Expected right hand side of expression(%s) to be same as left hand side(string)' % self.typeof(right, lineno))
            if self.typeof(left, lineno) == 'list':
                if self.typeof(right, lineno) != 'list':
                    error.throwType(lineno, 'Expected right hand side of expression(%s) to be same as left hand side(list)' % self.typeof(right, lineno))
        else:
            if self.typeof(left, lineno) == 'int':
                if self.typeof(right, lineno) != 'int':
                    error.throwType(lineno, 'Only allowed to have a number on the right hand side of a *, /, and -, not %s' % self.typeof(right, lineno))
            else:
                error.throwType(lineno, 'Only allowed to have number on the left hand side of a *, /, and -, not %s' % self.typeof(left, lineno))

    # FACTOR -> ( EXPR ) | INT | STR | ID | FuncCall
    def factor(self, start):
        self.index = start
        f1 = self.factor1(self.index)
        if f1 is not None:
            return f1
        self.index = start
        i = self.eatTyp('INT')
        if i is not None:
            node = IntegerNode(i)
            node.typ = 'int'
            return node
        self.index = start
        real = self.eatTyp('REAL')
        if real is not None:
            node = RealNode(real)
            node.typ = 'real'
            return node
        self.index = start
        s = self.eatTyp('STR')
        if s is not None:
            node = StringNode(s)
            node.typ = 'string'
            return node
        self.index = start
        func = self.funCall(self.index)
        if func is not None:
            node = func
            node.typ = self.symbolTable.get(func.name, self.tokens[self.index-1].lineno)[0]
            return node
        self.index = start
        indexed = self.indexed(self.index)
        if indexed is not None:
            return 'not known yet'
        ident = self.eatTyp('ID')
        if ident is not None:
            self.symbolTable.get(ident, self.tokens[self.index-1].lineno)
            identifier = IdentifierNode(ident)
            identifier.typ = self.symbolTable.get(ident, self.tokens[self.index-1].lineno)[0]
            return identifier
        self.index = start
        pi = self.eatVal('PI')
        if pi is not None:
            node = RealNode(3.141592653589793238462643)
            node.typ = 'real'
            return node
        self.index = start
        beginList = self.eatVal('[')
        if beginList is not None:
            list = self.callArgs(self.index)
            if list is not None:
                endList = self.eatVal(']')
                if endList is not None:
                    node = ListNode(list)
                    node.typ = 'list'
                    return node
        self.index = start
        neg = self.eatVal('-')
        if neg is not None:
            factor = self.factor(self.index)
            if factor is not None:
                node = NegativeNode(factor)
                node.typ = self.typeof(node.val, self.tokens[self.index-1].lineno)
                if node.typ != 'real' and node.typ != 'int':
                    error.throwType(self.tokens[self.index-1].lineno, 'Cannot make a negative out of something other than an integer or real')
                return node
        self.index = start
        return None

    def factor1(self, start):
        self.index = start
        lp = self.eatTyp('LP')
        if lp is None:
            self.index = start
            return None
        expr = self.expression(self.index)
        if expr is None:
            self.index = start
            return None
        rp = self.eatTyp('RP')
        if rp is None:
            self.index = start
            return None
        return expr

    def indexed(self, start):
        self.index = start
        id = self.eatTyp('ID')
        if id is None:
            self.index = start
            return None
        beginIndex = self.eatVal('[')
        if beginIndex is None:
            self.index = start
            return None
        expr = self.expression(self.index)
        if expr is None:
            self.index = start
            return None
        endIndex = self.eatVal(']')
        if endIndex is None:
            self.index = start
            return None
        return IndexedValNode(id, expr)

    # LoneFuncCall -> ID ( FARGS ) ;
    def loneFunCall(self, start):
        self.index = start
        built = ''
        builtin = False
        id = self.eatTyp('ID')
        if id is None:
            built = self.eatTyp('BUILT')
            if built is None:
                self.index = start
                return None
            id = built
            builtin = True
        lineno = self.tokens[self.index-1].lineno
        lp = self.eatVal('(')
        if lp is None:
            self.index = start
            return None
        args = self.callArgs(self.index)
        if args is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'arguments')
            return None
        lineno = self.tokens[self.index-1].lineno
        rp = self.eatVal(')')
        if rp is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'closing parenthesis')
            return None
        end = self.eatVal(';')
        if end is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'semi-colon')
            return None
        if builtin is True:
            if len(args) == self.builtins[built][1]:
                return self.builtins[built][0](args)
            else:
                error.throwArgument(lineno, 'Wrong amount of arguments for built-in function')
        self.symbolTable.get(id, lineno, len(args))
        details = self.symbolTable.get(id, lineno, len(args))
        for i, typ in enumerate(args):
            if self.typeof(typ, lineno) != details[0][i]:
                error.throwType(lineno, 'Wrong type for argument %d of function `%s\'' % (i+1, id))
        return FuncCallNode(id, args)

    # FuncCall -> ID ( FARGS ) ;
    def funCall(self, start):
        self.index = start
        built = ''
        builtin = False
        id = self.eatTyp('ID')
        if id is None:
            built = self.eatTyp('BUILT')
            if built is None:
                self.index = start
                return None
            id = built
            builtin = True
        lineno = self.tokens[self.index-1].lineno
        lp = self.eatVal('(')
        if lp is None:
            self.index = start
            return None
        args = self.callArgs(self.index)
        if args is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'arguments')
            return None
        rp = self.eatVal(')')
        if rp is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'closing parenthesis')
            return None
        if builtin is True:
            return self.builtins[built][0](args)
        details = self.symbolTable.get(id, lineno, len(args))
        for i, typ in enumerate(args, 1):
            if self.typeof(typ, lineno) != details[0][i][0]:
                error.throwType(lineno, 'Wrong type for argument %d of function `%s\'' % (i, id))
        return FuncCallNode(id, args)

    # ARGS -> TYPE ID ,*
    def args(self, start):
        self.index = start
        args = []
        while True:
            save = self.index
            typ = self.eatTyp('TYPE')
            if typ is None:
                self.index = save
                break
            expr = self.eatTyp('ID')
            if expr is None:
                self.index = save
                break
            cma = self.eatVal(',')
            args.append([typ, expr])
        return tuple(args)

    # FARGS -> EXPR , *
    def callArgs(self, start):
        self.index = start
        args = []
        while True:
            save = self.index
            expr = self.expression(self.index)
            if expr is None:
                self.index = save
                break
            cma = self.eatVal(',')
            try:
                args.append(expr.val)
            except AttributeError:
                args.append(expr)
        return tuple(args)

    # FuncDecl -> TYPE ID ( ARGS ) body
    def funcDecl(self, start):
        self.index = start
        typ = self.eatTyp('TYPE')
        if typ is None:
            self.index = start
            return None
        lineno = self.tokens[self.index-1].lineno
        id = self.eatTyp('ID')
        if id is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'identifier after type')
            return None
        lp = self.eatVal('(')
        if lp is None:
            self.index = start
            return None
        args = self.args(self.index)
        if args is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'function arguments')
            return None
        rp = self.eatVal(')')
        if rp is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'closing parenthesis')
            return None
        if self.inFunction:
            error.throwUnexpected(lineno, 'Cannot have nested functions')
            return None
        for arg in args:
            self.symbolTable.set(arg[1], arg[0])
        self.inFunction = True
        types = [typ]
        for arg in args:
            types.append(arg)
        self.symbolTable.set(id, types, len(args))
        self.function = id
        bd = self.body(self.index)
        if bd is None:
            self.index = start
            return None
        self.inFunction = False
        for arg in args:
            self.symbolTable.pop(arg[1])
        return FuncDeclarationNode(id, args, typ, bd)

    def ret(self, start):
        self.index = start
        key = self.eatTok(['KEY', 'return'])
        if key is None:
            self.index = start
            return None
        if not self.inFunction:
            error.throwUnexpected(self.tokens[self.index-1].lineno, 'Expected return statement to be in a function')
        expr = self.expression(self.index)
        if expr is None:
            expr = 'none'
        end = self.eatVal(';')
        if end is None:
            self.index = start
            error.throwExpected(self.tokens[self.index-1].lineno, 'semi-colon in return statement')
            return None
        retType = self.typeof(expr, self.tokens[self.index-2].lineno)
        funcType = self.symbolTable.get(self.function, self.tokens[self.index-2].lineno)[0][0]
        if retType != funcType:
            error.throwType(self.tokens[self.index-2].lineno, 'Return type of function `%s\'(%s) not same as type returned(%s)' % (self.function, funcType, retType))
        return RetNode(expr)

    # block -> { Program }
    def body(self, start):
        self.index = start
        op = self.eatVal('{')
        if op is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'opening curly brace in a body')
            return None
        i = self.index
        while self.tokens[i].val != '}':
            i += 1
        program = self.program(i)
        if program is None:
            self.index = start
            return None
        cl = self.eatVal('}')
        if cl is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'closing curly brace in a body')
            return None
        return program

    # VarDecl -> TYPE ID = EXPR ;
    def varDecl(self, start):
        self.index = start
        typ = self.eatTyp('TYPE')
        if typ is None:
            self.index = start
            return None
        id = self.eatTyp('ID')
        if id is None:
            self.index = start
            return None
        assign = self.eatTyp('ASSIGN')
        if assign is None:
            self.index = start
            return None
        expr = self.expression(self.index)
        if expr is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'expression after assignment operator')
            return None
        end = self.eatVal(';')
        if end is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'semicolon in var declaration')
            return None
        self.symbolTable.set(id, typ)
        if expr.typ != typ.lower():
            error.throwType(self.tokens[self.index-1].lineno, 'Type for `%s\'(%s) not same as type of expression(%s)' % (id, typ, expr.typ))
        return VarDeclarationNode(id, typ, expr)

    def emptyVar(self, start):
        self.index = start
        typ = self.eatTyp('TYPE')
        if typ is None:
            self.index = start
            return None
        id = self.eatTyp('ID')
        if id is None:
            self.index = start
            return None
        end = self.eatVal(';')
        if end is None:
            self.index = start
            lp = self.eatVal('(')
            if lp is None:
                self.index = start
                return None
        self.symbolTable.set(id, typ)
        return VarDeclarationNode(id, typ, 'none')

    def varAssign(self, start):
        self.index = start
        id = self.eatTyp('ID')
        if id is None:
            self.index = start
            return None
        lineno = self.tokens[self.index-1].lineno
        assign = self.eatTyp('ASSIGN')
        if assign is None:
            self.index = start
            return None
        expr = self.expression(self.index)
        if expr is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'expression after assignment operator')
            return None
        end = self.eatVal(';')
        if end is None:
            self.index = start
            error.throwExpected(self.tokens[self.index].lineno, 'semicolon in var declaration')
            return None
        typ = self.symbolTable.get(id, lineno)[0]
        if expr.typ != typ.lower():
            error.throwType(self.tokens[self.index-1].lineno, 'Type for `%s\'(%s) not same as type of expression(%s)' % (id, typ, expr.typ))
        return VarAssignmentNode(id, expr)

    # Statement -> VarDecl | EmptyVar | VarAssign | FuncDecl | FuncCall
    def statement(self):
        start = self.index
        return self.varDecl(start) or self.emptyVar(start) or self.varAssign(start) or self.funcDecl(start) or self.loneFunCall(start) or self.ret(start)

    # Program -> Statement*
    def program(self, maxIndex=None):
        if maxIndex is None:
            maxIndex = len(self.tokens)
        values = []
        table = self.symbolTable.table.copy()
        while self.index < maxIndex:
            save = self.index
            st = self.statement()
            if st is not None:
                values.append(st)
            else:
                error.throwUnexpected(self.tokens[self.index].lineno, 'Unexpected token `%s\'' % self.tokens[self.index].val)
                self.index = save
                break
        self.symbolTable.table = table
        return values

    # S' -> program
    def parse(self, tokens):
        self.tokens = tokens
        program = self.program()
        if program is not None:
            return program
        else:
            return
