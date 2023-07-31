from parser_1 import *
from typing import Optional, Dict, Tuple, List
from z3 import Int, Solver, sat

COMP_OPS_OPPOSITES = {
    '==': '!=',
    '!=': '==',
    '<': '>=',
    '>': '<=',
    '<=': '>',
    '>=': '<'
}

Comparisons = List[Tuple[str, 'Polynomial', 'Polynomial']]
Variables = Dict[str, 'Variable']

# Assume each variable gets assigned input() only once
# Assume variables don't get multiplied by each other
# _ after variable name means it's the value received from input()
# The code is quite inefficient, it's exponential in the number of if statements in the program,
# but can be improved by branch pruning

class InputVariable:
    def __init__(self, name: str):
        self.name: str = name

    def __str__(self) -> str:
        return self.name

class PolynomialTerm:
    '''
    Represents a non-constant term in a polynomial.\n
    e.g. 2*x in the polynomial 3*y + 2*x + 1
    '''
    def __init__(self, variable: InputVariable, coefficient: int, power: int):
        self.variable: InputVariable = variable
        self.coefficient: int = coefficient
        self.power: int = power

    def __str__(self) -> str:
        if self.coefficient == 0:
            return "0"
        if self.power == 0:
            return str(self.coefficient)
        string: str = self.variable.name
        if self.coefficient != 1:
            string = str(self.coefficient) + "*" + string
        if self.power != 1:
            string += "^" + str(self.power)
        return string

    def __neg__(self) -> 'PolynomialTerm':
        return PolynomialTerm(self.variable, -self.coefficient, self.power)
    
    def copy(self) -> 'PolynomialTerm':
        return PolynomialTerm(self.variable, self.coefficient, self.power)
    
    def is_zero(self) -> None:
        return self.coefficient == 0

class Polynomial:
    def __init__(self, terms: List[PolynomialTerm], constant: int):
        self.terms: List[PolynomialTerm] = terms
        self.constant: int = constant

    @staticmethod
    def from_constant(constant: int) -> 'Polynomial':
        return Polynomial([], constant)
    
    @staticmethod
    def from_one_var(name: str) -> 'Polynomial':
        return Polynomial([PolynomialTerm(InputVariable(name), 1, 1)], 0)
    
    def is_constant(self) -> bool:
        return self.terms == []

    def __str__(self) -> str:
        if len(self.terms) == 0:
            return str(self.constant)
        string: str = " + ".join([str(term) for term in self.terms])
        return string + " + " + str(self.constant) if self.constant != 0 else string
    
    def deep_copy(self) -> 'Polynomial':
        return Polynomial([term.copy() for term in self.terms], self.constant)
    
    def __add__(self, other: 'Polynomial') -> 'Polynomial':
        for other_term in other.terms:
            for self_term in self.terms:
                if self_term.variable == other_term.variable and self_term.power == other_term.power:
                    self_term.coefficient += other_term.coefficient
                    break
            else:
                self.terms.append(other_term)

        self.constant += other.constant
        return self
        
    def __neg__(self) -> 'Polynomial':
        return Polynomial([-term for term in self.terms], -self.constant)
    
    def __sub__(self, other: 'Polynomial') -> 'Polynomial':
        return self + (-other)
    
    def __mul__(self, other: 'Polynomial') -> 'Polynomial':
        if self.is_constant():
            ret: Polynomial = Polynomial([term.copy() for term in other.terms], self.constant * other.constant)
            for term in ret.terms:
                term.coefficient *= self.constant
            return ret
        elif other.is_constant():
            ret: Polynomial = Polynomial([term.copy() for term in self.terms], self.constant * other.constant)
            for term in ret.terms:
                term.coefficient *= other.constant
            return ret
        print("Multiplication of 2 variables is not supported")
        return self


class Variable:
    def __init__(self, name: str, polynomial: Optional[Polynomial] = None):
        self.name: str = name
        self.value: Optional[Polynomial] = polynomial
        self.just_int_holder: bool = False
    
    def deep_copy(self) -> 'Variable':
        copy: Variable = Variable(self.name)
        if self.value is not None:
            copy.value = self.value.deep_copy()
        copy.just_int_holder = self.just_int_holder
        return copy
    
    def __str__(self) -> str:
        return self.name + " = " + str(self.value)


def to_Variable(x: Value, variables: Variables) -> Union[Variable, Value]:
    if isinstance(x, str):
        x: Variable = variables[x].deep_copy()
    if isinstance(x, int):
        x: Variable = Variable("Int"+str(x), Polynomial.from_constant(x))
        x.just_int_holder = True
    return x


def branching(condition: Comp, variables: Variables, 
              comparisons: Comparisons) \
                -> Tuple[Comparisons, Comparisons, 
                         Variables, Variables]:
    '''
    Fork the current state of the program into 2 states - one where the condition is true and one where it's false
    '''

    lhs: Variable = to_Variable(condition.l, variables)
    rhs: Variable = to_Variable(condition.r, variables)

    comparisons_t = comparisons
    comparisons_f = [(op, opd1, opd2) for (op, opd1, opd2) in comparisons]
    comparisons_t.append((condition.op, lhs.value, rhs.value))
    comparisons_f.append((COMP_OPS_OPPOSITES[condition.op], lhs.value, rhs.value))

    new_vars_if: Variables = variables
    new_vars_nif: Variables = {k: v.deep_copy() for k, v in variables.items()}

    return comparisons_t, comparisons_f, new_vars_if, new_vars_nif


def if_command(program: Program, commandsIndex: int, variables: Variables,
               comparisons: Comparisons) -> bool:
    if_com: Command = program.commands[commandsIndex]

    comparisons_if, comparisons_nif, \
        new_vars_if, new_vars_nif = branching(if_com.condition, variables, comparisons)

    # If the if is successful then execute the if body 
    for assignment_command in if_com.body:
        assignment(assignment_command, new_vars_if)

    return is_assert_true(program, commandsIndex + 1, new_vars_if, comparisons_if) \
        and is_assert_true(program, commandsIndex + 1, new_vars_nif, comparisons_nif)


def assignment(command: Assignment, variables: Variables) -> None:
    rhs = command.rhs
    if isinstance(rhs, Expr):
        rhs_l = to_Variable(rhs.l, variables)
        rhs_r = to_Variable(rhs.r, variables)
        if rhs.op == '+':
            rhs_l.value = rhs_l.value + rhs_r.value
        elif rhs.op == '-':
            rhs_l.value = rhs_l.value - rhs_r.value
        elif rhs.op == '*':
            rhs_l.value = rhs_l.value * rhs_r.value
        else:
            print("Operator " + rhs.op + " is not supported")
        rhs = rhs_l
    elif isinstance(rhs, Input):
        rhs: Variable = Variable(command.lhs, Polynomial.from_one_var(command.lhs + "_"))
    else:
        rhs = to_Variable(rhs, variables)

    rhs.name = command.lhs
    rhs.just_int_holder = False
    variables[command.lhs] = rhs


def parse_rhs(rhs: Polynomial, variables: Variables):
    value = rhs.constant
    for part in rhs.terms:
        value += part.coefficient * variables[part.variable.name]
    return value

def satisfiable(input_variables: Set[str],
                comparisons: Comparisons) -> bool:
    '''
    Check if the system of equations and inequalities in comparisons has any solution using z3\n
    input_variables is a set of all the variables that appear in the system
    '''
    variables = {}
    for var in input_variables:
        variables[var] = Int(var)

    solver = Solver()
        
    for comparison in comparisons:
        op, opd1, opd2 = comparison
        solver.add(parse_rhs(opd1, variables) < parse_rhs(opd2, variables) if op == '<' else
                   parse_rhs(opd1, variables) > parse_rhs(opd2, variables) if op == '>' else
                   parse_rhs(opd1, variables) <= parse_rhs(opd2, variables) if op == '<=' else
                   parse_rhs(opd1, variables) >= parse_rhs(opd2, variables) if op == '>=' else
                   parse_rhs(opd1, variables) == parse_rhs(opd2, variables) if op == '==' else
                   parse_rhs(opd1, variables) != parse_rhs(opd2, variables))
    
    # print(solver)
    if solver.check() == sat:
        # print("Counterexample: ")
        # for var in solver.model():
        #     if var.name()[-1] == "_":
        #         print(var.name()[:-1], "=", solver.model()[var])
        return True
    else:
        return False


def is_assert_true(program: Program, commandsIndex: int, 
           variables: Variables, comparisons: Comparisons) -> List[Variable]:

    for i in range(commandsIndex, len(program.commands)):
        command = program.commands[i]
        if type(command) == If:
            return if_command(program, i, variables, comparisons)
        elif type(command) == Assignment:
            assignment(command, variables)

    # Add the opposite of the post condition
    _, comparisons_f, _, _ = branching(program.postCondition, variables, comparisons)

    # Add final values of variables
    for var in variables.values():
        comparisons_f.append(('==', Polynomial.from_one_var(var.name), var.value.deep_copy()))

    # Now check if the constraints from the program AND the opposite of the post condition are satisfiable
    all_variables: Set[str] = {prg_var + "_" for prg_var in program.variables}.union({x.name for x in variables.values()})
    return not satisfiable(all_variables, comparisons_f)



def main() -> None:
    for i in range(1, 31):
        print("Test", i)
        if is_assert_true(parse_file(f"programs/other/{i}.txt"), 0, {}, []):
            print("ok")
        else:
            print("nok")
        
        # print("-------------------------------------------")

main()