import operator as op
import sys

class DupSpace_VM():
    def __init__(self):
        self.namespaces = {
            'default': {
                'stack': [],
                'ret_stack': [],
                'vars': {},
                'funs': {},
            }
        }
        # -------------------------------------- Current namespace pointer
        self.cur_namespace = self.namespaces['default']

        self.funs = {
            # ---------------------------------- OPS
            '+': op.add, '-': op.sub,
            '*': op.mul, '/': op.truediv,
            '<': op.lt, '>': op.gt,
            '>=': op.ge, '<=': op.le, 
            '=': op.eq, 'eq?': op.is_,
            ';': lambda *args: None,
            # ---------------------------------- STACK OPERATIONS
            'push': self._push, 'pop': self._pop,
            'dup': self._dup, 'swap': self._swap,
            'over': self._over, 'drop': self._drop,
            'depth': self._depth, 'clear': self._clear,
            '>ret': self.to_ret_stack, 
            'ret>': self.from_ret_stack, 
            'ret@': self.latest_ret_stack,
            # ---------------------------------- MAIN
            'set': self._set,
            'namespace': self._namespace,
            # ---------------------------------- IO
            'print': print, 'input': input,
            # ---------------------------------- TYPES
            'is_int?': lambda x: isinstance(x, int),
            'is_str?': lambda x: isinstance(x, str),
            'is_float?': lambda x: isinstance(x, float),
            'is_bool?': lambda x: isinstance(x, bool),
            'is_null?': lambda x: x == [],
            'to_int': int, 'to_str': str,
            'to_float': float, 'to_bool': bool,
            # ---------------------------------- FUNCTIONS
            'len': len, 'map': map,
            'min': min, 'max': max,
            'begin': lambda *x: x[-1],
            'car': lambda x: x[0],
            'cdr': lambda x: x[1:],
            'cons': lambda x, y: [x] + y,
            'eval': self.execute,
            'apply': lambda f, args: f(*args) if callable(f) else self.execute([f] + args),
            'split': self._split,
            # ---------------------------------- ERRORS
            'warn': self._warn,
            'raise': self._raise,
        }
        self.warns = {
            'StackOperationWarning',
        }
        self.errors = {
            'EmptyStackError',
        }
    def _push(self, *args):
        self.cur_namespace['stack'].append(*args)

    def _pop(self):
        if len(self.cur_namespace['stack']) >= 1:
            return self.cur_namespace['stack'].pop()
        else:
            self._warn('StackOperationWarning','Cannot do operation "op", stack is empty.')

    def _dup(self):
        if len(self.cur_namespace['stack']) >= 1:
            return self.cur_namespace['stack'].append(self.cur_namespace['stack'][-1])
        else:
            self._warn('StackOperationWarning','Cannot do operation "dup", stack is empty.')

    def _swap(self):
        if len(self.cur_namespace['stack']) >= 2:
            a = self.cur_namespace['stack'].pop()
            b = self.cur_namespace['stack'].pop()
            self.cur_namespace['stack'].append(a)
            self.cur_namespace['stack'].append(b)
        else:
            self._warn('StackOperationWarning','Cannot do operation "swap", stack is empty.')

    def _over(self):
        if len(self.cur_namespace['stack']) >= 2:
            self.cur_namespace['stack'].append(self.cur_namespace['stack'][-2])
        else:
            self._warn('StackOperationWarning','Cannot do operation "over", stack is empty.')

    def _drop(self):
        if len(self.cur_namespace['stack']) >= 1:
            self.cur_namespace['stack'].pop()
        else:
            self._warn('StackOperationWarning','Cannot do operation "drop", stack is empty.')

    def _depth(self):
        self.cur_namespace['stack'].append(len(self.cur_namespace['stack']))

    def _clear(self):
        self.cur_namespace['stack'].clear()
    
    def to_ret_stack(self):
        if len(self.cur_namespace['stack']) >= 1:
            self.cur_namespace['ret_stack'].append(self.cur_namespace['stack'].pop())
        else:
            self._warn('StackOperationWarning','Cannot transfer object from stack to return stack, stack is empty.')

    def from_ret_stack(self):
        if len(self.cur_namespace['ret_stack']) >= 1:
            self.cur_namespace['stack'].append(self.cur_namespace['ret_stack'].pop())
        else:
            self._warn('StackOperationWarning','Cannot transfer object from return stack, stack is empty.')

    def latest_ret_stack(self):
        if len(self.cur_namespace['ret_stack']) >= 1:
            self.cur_namespace['stack'].append(self.cur_namespace['ret_stack'][-1])
        else:
            self._warn('StackOperationWarning','Cannot copy latest object from return stack to stack, return stack is empty.')

    def _split(self, *args):
        if isinstance(args[0], list):
            return args[0].split()

    def _set(self, *args):
        if args[0] in self.cur_namespace['funs']:
            del self.cur_namespace['funs'][args[0]]
        self.cur_namespace['vars'][args[0]] = args[1]

    def _namespace(self, arg):
        if arg in self.namespaces:
            self.cur_namespace = self.namespaces[arg]
        else:
            self.namespaces[arg] = {
                'stack': [],
                'ret_stack': [],
                'vars': {},
                'funs': {},
            }
            self.cur_namespace = self.namespaces[arg]

    def _warn(self, *args):
        if args[0] in self.warns:
            print(f'{args[0]}: {args[1]}')

    def _raise(self, *args):
        if args[0] in self.errors:
            print(f'{args[0]}: {args[1]}')
            exit(1)

    def execute(self, expr):
        if not isinstance(expr, list):
            if isinstance(expr, str):
                if '::' in expr:
                    parts = expr.split('::')
                    if parts[0] in self.namespaces:
                        if parts[1] in self.namespaces[parts[0]]['vars']:
                            return self.namespaces[parts[0]]['vars'][parts[1]]
                        elif parts[1] in self.namespaces[parts[0]]['funs']:
                            return self.execute(self.namespaces[parts[0]]['funs'][parts[1]])
                if expr in self.cur_namespace['vars']:
                    return self.cur_namespace['vars'][expr]
                elif expr in self.cur_namespace['funs']:
                    return self.execute(self.cur_namespace['funs'][expr])
                else:
                    return expr
            else:
                return expr
        op_ = expr[0]
        # ---------------------------------------------------------------------------------------------- QUOTE
        if op_ == 'quote':
            return expr[1]
        # ---------------------------------------------------------------------------------------------- IF
        elif op_ == 'if':
            condition = self.execute(expr[1])
            if condition:
                return self.execute(expr[2])
            else:
                return self.execute(expr[3])
        # ---------------------------------------------------------------------------------------------- DEF
        elif op_ == 'def':
            name = expr[1]
            if name in self.cur_namespace['vars']:
                del self.cur_namespace['vars'][name]
            body = expr[2]
            self.cur_namespace['funs'][name] = body
            return None
        # ---------------------------------------------------------------------------------------------- REPEAT
        elif op_ == 'repeat':
            value = self.execute(expr[1])
            body = expr[2]
            for _ in range(value):
                self.execute(body)
            return None
        # ---------------------------------------------------------------------------------------------- WHILE
        elif op_ == 'while':
            expr_ = self.execute(expr[1])
            body = expr[2]
            while expr_:
                expr_ = self.execute(expr[1])
                if expr_ == False: break
                self.execute(body)
            return None

        content_ = [self.execute(arg) for arg in expr[1:]]
        if op_ in self.funs:
            return self.funs[op_](*content_)
        elif op_ in self.cur_namespace['funs']:
            return self.execute(self.cur_namespace['funs'][op_])

def read_from_toks(tokens):
    if len(tokens) == 0:
        raise SyntaxError('Unexpected EOF while reading')
    token = tokens.pop(0)
    if '(' == token:
        L = []
        while tokens[0] != ')':
            L.append(read_from_toks(tokens))
        tokens.pop(0)
        return L
    elif ')' == token:
        raise SyntaxError('Unexpected )')
    else:
        try: return int(token)
        except ValueError:
            try: return float(token)
            except ValueError:
                return str(token)

# ------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        program = f.read()
    tokens = program.replace('(', ' ( ').replace(')',' ) ').split()
    vm = DupSpace_VM()
    while tokens:
        vm.execute(read_from_toks(tokens))
