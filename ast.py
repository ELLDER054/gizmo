ass AstNode(object):
    def toStr(self, prefix=""):
        s = "%s%s:" % (prefix, self.__class__.__name__)
        for prop in vars(self):
            val = getattr(self, prop)

            if not isinstance(val, list):
                val = [val]

            for v in val:
                if isinstance(v, AstNode):
                    valstr = "\n" + v.toStr(prefix+"\t\t")
                else:
                    valstr = str(v)
                s += "\n%s\t%s: %s" % (prefix, prop, valstr)
        return s


class VarDeclarationNode(AstNode):
    def __init__(self, name, typ, value):
        self.name = name
        self.type = typ
        self.value = value


class VarAssignmentNode(AstNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class FuncDeclarationNode(AstNode):
    def __init__(self, name, args, typ, body):
        self.name = name
        self.args = args
        self.type = typ
        self.body = body


class FuncCallNode(AstNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args


class IntegerNode(AstNode):
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return str(self.val)


class RealNode(AstNode):
    def __init__(self, val):
        self.val = val


class ListNode(AstNode):
    def __init__(self, list):
        self.list = list


class NegativeNode(AstNode):
    def __init__(self, val):
        self.val = val


class IndexedValNode(AstNode):
    def __init__(self, id, index):
        self.id = id
        self.index = index


class StringNode(AstNode):
    def __init__(self, val):
        self.val = val


class ExprNode(AstNode):
    def __init__(self, expr):
        self.expr = expr


class RetNode(AstNode):
    def __init__(self, expr):
        self.expr = expr


class IdentifierNode(AstNode):
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return self.val


class OperatorNode(AstNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return "\'%s %s %s\'" % (self.left, self.op, self.right)


class WriteNode(AstNode):
    def __init__(self, val):
        self.val = val


class ReadNode(AstNode):
    def __init__(self, ask):
        self.ask = ask
