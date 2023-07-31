from parser_1 import *

from typing import Optional, Dict, Tuple



class Variable:
    def __init__(self, string: str="", value: Optional[int]=None, 
                 lb: int=float("-inf"), rb: int=float("inf"), 
                 lb_included: bool=False, rb_included: bool=False):
        self.string: str = string
        self.left_bound: int = lb
        self.right_bound: int = rb
        self.value: Optional[int] = value
        self.lb_included: bool = lb_included
        self.rb_included: bool = rb_included

    def set_value(self, value: int) -> None:
        self.value = value
        self.left_bound = value
        self.right_bound = value
        self.rb_included = True
        self.lb_included = True
    
    def copy(self) -> 'Variable':
        return Variable(self.string, self.value, self.left_bound, self.right_bound, self.lb_included, self.rb_included)
    
    def set_boundless(self) -> None:
        self.left_bound = float("-inf")
        self.right_bound = float("inf")
        self.lb_included = False
        self.rb_included = False

    def inverse_copy(self) -> 'Variable':
        if self.perfect():
            return self.copy()
        return Variable(self.string, None, self.right_bound, self.left_bound,
                        False if self.right_bound == float("inf") else not self.rb_included,
                        False if self.left_bound == float("-inf") else not self.lb_included)

    def complement(self) -> List['Variable']:
        res: List['Variable'] = []
        if self.left_bound != float("-inf"):
            res.append(Variable(self.string, None, float("-inf"), self.left_bound, False, not self.lb_included))
        if self.right_bound != float("inf"):
            res.append(Variable(self.string, None, self.right_bound, float("inf"), not self.rb_included, False))
        return res
    
    def except_var(self, other: 'Variable') -> List['Variable']:
        res: List[Variable] = []
        if self.left_bound < other.left_bound:
            res.append(Variable(self.string, None, self.left_bound, other.left_bound, self.lb_included, not other.lb_included))
        if self.right_bound > other.right_bound:
            res.append(Variable(self.string, None, other.right_bound, self.right_bound, not other.rb_included, self.rb_included))
        return res
    
    def perfect(self) -> bool:
        return self.left_bound == self.right_bound and (self.lb_included or self.rb_included)

    def __str__(self):
        left: str = "<" if self.lb_included else "("
        right: str = ">" if self.rb_included else ")"
        return f"{self.string} {left}{self.left_bound} - {self.right_bound}{right}"

    def __add__(self, o) -> 'Variable':
        new_variable = self.copy()
        if type(o) == int:
            if self.perfect():
                assert new_variable.perfect()
                new_variable.value += o
                new_variable.left_bound += o
                new_variable.right_bound += o
            else:
                new_variable.left_bound = self.left_bound + o
                new_variable.right_bound =self.right_bound + o
        elif type(o) == Variable:
            new_variable.left_bound = self.left_bound + o.left_bound
            new_variable.right_bound = self.right_bound + o.right_bound
            if new_variable.lb_included and o.lb_included:
                new_variable.lb_included = True
            else:
                new_variable.lb_included = False
            if new_variable.rb_included and o.rb_included:
                new_variable.rb_included = True
            else:
                new_variable.rb_included = False
        elif type(o) == Input:
            new_variable.set_boundless()
        return new_variable
    

    def __sub__(self, o) -> 'Variable':
        if type(o) == int:
            return self + (-o)
        
        new_variable = self.copy()
        if type(o) == Input:
            new_variable.set_boundless()
        elif type(o) == Variable:
            new_variable.left_bound = self.left_bound - o.right_bound
            new_variable.right_bound = self.right_bound - o.left_bound
            if new_variable.lb_included and o.rb_included:
                new_variable.lb_included = True
            else:
                new_variable.lb_included = False
            if new_variable.rb_included and o.lb_included:
                new_variable.rb_included = True
            else:
                new_variable.rb_included = False
        return new_variable
    

    def assign(self, o) -> None:
        if type(o) == int:
            self.set_value(o)
        elif type(o) == Variable:
            self = o.copy()
        # elif type(o) == Input:
        return self.set_boundless()


    def __eq__(self, o) -> Tuple['Variable', Optional['Variable']]:
        if isinstance(o, int):
            if self.perfect():
                if self.value == o:
                    return self.copy(), None
                else:
                    return NOTHING, None
            if self.left_bound < o and self.right_bound > o \
                or (self.lb_included and o == self.left_bound) \
                or (self.rb_included and o == self.right_bound):
                return Variable(self.string, o, o, o, True, True), None
            return NOTHING, None
        if isinstance(o, Input):
            return self.copy(), None
        if isinstance(o, Variable):
            if self.perfect() and o.perfect():
                if self.value == o.value:
                    return self.copy(), o.copy()
                else:
                    return NOTHING, NOTHING
            if self.perfect():
                return o == self.value
            if o.perfect():
                return self == o.value
            
            self_copy: Variable = self.copy()
            o_copy: Variable = o.copy()
            if self.left_bound < o.left_bound:
                self_copy.left_bound = o.left_bound
                self_copy.lb_included = o.lb_included
            elif self.left_bound > o.left_bound:
                o_copy.left_bound = self.left_bound
                o_copy.lb_included = self.lb_included
            else:
                self_copy.lb_included = self.lb_included and o.lb_included
                o_copy.lb_included = self.lb_included and o.lb_included

            if self.right_bound < o.right_bound:
                o_copy.right_bound = self.right_bound
                o_copy.rb_included = self.rb_included
            elif self.right_bound > o.right_bound:
                self_copy.right_bound = o.right_bound
                self_copy.rb_included = o.rb_included
            else:
                self_copy.rb_included = self.rb_included and o.rb_included
                o_copy.rb_included = self.rb_included and o.rb_included
            return self_copy, o_copy


    def __lt__(self, o) -> Tuple['Variable', 'Variable']:
        if isinstance(o, int):
            if self.perfect():
                if self.value < o:
                    return self.copy(), None
                else:
                    return NOTHING, None

            if self.left_bound >= o:
                return NOTHING, None
            
            ret: Variable = self.copy()
            ret.right_bound = o
            ret.rb_included = False
            return ret, None

        elif type(o) == Variable:
            self_copy: Variable = self.copy()
            o_copy: Variable = o.copy()
            self_copy.right_bound = min(o.right_bound, self_copy.right_bound)
            if self_copy.rb_included:
                self_copy.rb_included = o.rb_included

            o_copy.left_bound = max(o.left_bound, self_copy.left_bound)
            if o_copy.lb_included:
                o_copy.lb_included = self_copy.lb_included
            return self_copy, o_copy
    
        # elif type(o) == Input:
        return self.copy(), None


    def __le__(self, o) -> Tuple['Variable', 'Variable']:
        ret, o = self < o
        ret.rb_included = True
        return ret, o


    def __gt__(self, o) -> 'Variable':
        if isinstance(o, int):
            if self.perfect():
                print(self)
                if self.value > o:
                    return self.copy(), None
                else:
                    return NOTHING, None

            if self.right_bound <= o:
                return NOTHING, None        
            ret: Variable = self.copy()
            ret.left_bound = o
            ret.lb_included = False
            return ret, None
        
        elif type(o) == Variable:
            self_copy: Variable = self.copy()
            o_copy: Variable = o.copy()
            self_copy.left_bound = max(o.left_bound, self_copy.left_bound)
            if self_copy.lb_included:
                self_copy.lb_included = o.lb_included

            o_copy.right_bound = min(o.right_bound, self_copy.right_bound)
            if o_copy.rb_included:
                o_copy.rb_included = self_copy.rb_included
            return self_copy, o_copy

        # elif type(o) == Input:
        return self.copy(), None


    def __ge__(self, o) -> 'Variable':
        ret, o = self > o
        ret.lb_included = True
        return ret, o
    
    def possible(self) -> bool:
        if self.left_bound > self.right_bound:
            return False
        if self.left_bound == self.right_bound and not self.lb_included and not self.rb_included:
            return False
        return True


NOTHING = Variable("-", None, 0, 0, False, False)


def comp(variables: Dict[str, Variable], condition: Comp) -> Optional[Tuple[Variable, Variable]]:
    right: Variable = NOTHING.copy()
    left: Variable = NOTHING.copy()
    right_new: Optional[Variable] = None
    left_new: Variable = NOTHING.copy()
    if isinstance(condition.r, str):
        right = variables[condition.r]
    else:
        right = condition.r
    if isinstance(condition.l, str):
        left = variables[condition.l]
    else:
        left = condition.l
    if condition.op == '==':
        left_new, right_new = left == right
    if condition.op == '<':
        left_new, right_new = left < right
    if condition.op == '>':
        left_new, right_new = left > right
    if condition.op == '<=':
        left_new, right_new = left <= right
    if condition.op == '>=':
        left_new, right_new = left >= right
    
    if not left_new.possible():
        return None
    if right_new is not None and not right_new.possible():
        return None
    
    return left_new, right_new


def branching(program: Program, commandsIndex: int, variables: Dict[str, Variable]) -> bool:
    comparison_command: Command = program.commands[commandsIndex]
    comp_result: Optional[Tuple[Variable, Variable]] = comp(variables, comparison_command.condition)
    if comp_result is None:
        return check_assert(program, commandsIndex + 1, variables)

    left, right = comp_result

    new_variables: Dict[str, Variable] = variables.copy()
    new_variables[left.string] = left
    if right is not None:
        new_variables[right.string] = right
    for assignment_command in comparison_command.body:
        assignment(assignment_command, new_variables)
    if not check_assert(program, commandsIndex + 1, new_variables):
        return False
    
    left_excepts: List[Variable] = []
    right_excepts: List[Variable] = []
    if isinstance(comparison_command.condition.l, str):
        left_excepts = variables[comparison_command.condition.l].except_var(left)
    else:
        left_excepts.append(NOTHING)
    if isinstance(comparison_command.condition.r, str):
        right_excepts = variables[comparison_command.condition.r].except_var(right)
    else:
        right_excepts.append(NOTHING)

    for left_except in left_excepts:
        for right_except in right_excepts:
            new_variables = variables.copy()
            new_variables[left_except.string] = left_except
            new_variables[right_except.string] = right_except
            if not check_assert(program, commandsIndex + 1, new_variables):
                return False
    
    return True


def assignment(command: Command, variables: Dict[str, Variable]) -> None:
    rhs = command.rhs
    while isinstance(rhs, Expr):
        if isinstance(rhs.l, str):
            rhs.l = variables[rhs.l]
        if isinstance(rhs.r, str):
            rhs.r = variables[rhs.r]
        if rhs.op == '+':
            rhs = rhs.l + rhs.r
        elif rhs.op == '-':
            rhs = rhs.l - rhs.r
    if isinstance(rhs, str):
        rhs = variables[rhs]
    if isinstance(rhs, Variable):
        rhs = rhs.copy()
        rhs.string = command.lhs
    if isinstance(rhs, Input):
        rhs = NOTHING.copy()
        rhs.set_boundless()
        rhs.string = command.lhs
    if isinstance(rhs, int):
        rhs = Variable(command.lhs, rhs, rhs, rhs, True, True)

    variables[command.lhs] = rhs


def check_assert(program: Program, commandsIndex: int, variables: Dict[str, Variable]) -> bool:
    commands: List[Command] = program.commands
    postCondition: Comp = program.postCondition

    for i in range(commandsIndex, len(commands)):
        command = commands[i]
        if type(command) == If:
            return branching(program, i, variables)
        elif type(command) == Assignment:
            assignment(command, variables)

    print(commandsIndex)
    for x in variables:
        print(variables[x])
    print("------")

    if isinstance(postCondition.l, str):
        postCondition.l = variables[postCondition.l]
    if isinstance(postCondition.r, str):
        postCondition.r = variables[postCondition.r]

    comp_result = comp(variables, postCondition)
    if comp_result is None:
        return False
    left, right = comp_result

    return (isinstance(left, int) or left is None or postCondition.l.except_var(left) == []) \
        and (isinstance(right, int) or right is None or postCondition.r.except_var(right) == [])


def main(program: Program) -> bool:
    variables: Dict[str, Variable] = {}
    res: bool = check_assert(program, 0, variables)
    return res
    

for i in range(4, 30):
    if i in (3, 7, 8, 9):
        continue
    print("Test", i)
    print("-------------------------------------------")
    print(main(parse_file(f"programs/other/{i}.txt")))
    print("-------------------------------------------")
