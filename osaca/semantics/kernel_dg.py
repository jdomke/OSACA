#!/usr/bin/env python3

import copy
from itertools import chain, product

import networkx as nx

from osaca.parser import AttrDict
from osaca.semantics import MachineModel


class KernelDG(nx.DiGraph):
    def __init__(self, parsed_kernel, parser, hw_model: MachineModel):
        self.kernel = parsed_kernel
        self.parser = parser
        self.model = hw_model
        self.dg = self.create_DG(self.kernel)
        self.loopcarried_deps = self.check_for_loopcarried_dep(self.kernel)

    def create_DG(self, kernel):
        # 1. go through kernel instruction forms (as vertices)
        # 2. find edges (to dependend further instruction)
        # 3. get LT value and set as edge weight
        # 4. add instr forms as node attribute
        dg = nx.DiGraph()
        for i, instruction_form in enumerate(kernel):
            dg.add_node(instruction_form['line_number'])
            dg.nodes[instruction_form['line_number']]['instruction_form'] = instruction_form
            for dep in self.find_depending(instruction_form, kernel[i + 1:]):
                dg.add_edge(
                    instruction_form['line_number'],
                    dep['line_number'],
                    latency=instruction_form['latency'],
                )
                dg.nodes[dep['line_number']]['instruction_form'] = dep
        return dg

    def check_for_loopcarried_dep(self, kernel):
        multiplier = len(kernel) + 1
        # increase line number for second kernel loop
        kernel_length = len(kernel)
        first_line_no = kernel[0].line_number
        kernel_copy = [AttrDict.convert_dict(d) for d in copy.deepcopy(kernel)]
        tmp_kernel = kernel + kernel_copy
        for i, instruction_form in enumerate(tmp_kernel[kernel_length:]):
            tmp_kernel[i + kernel_length].line_number = instruction_form.line_number * multiplier
        # get dependency graph
        dg = self.create_DG(tmp_kernel)

        # build cyclic loop-carried dependencies
        loopcarried_deps = [
            (node, list(nx.algorithms.simple_paths.all_simple_paths(dg, node, node * multiplier)))
            for node in dg.nodes
            if node < first_line_no * multiplier
        ]
        # filter others and create graph
        loopcarried_deps = list(
            chain.from_iterable(
                [list(product([dep_chain[0]], dep_chain[1])) for dep_chain in loopcarried_deps]
            )
        )
        # adjust line numbers
        # and add reference to kernel again
        loopcarried_deps_dict = {}
        for dep in loopcarried_deps:
            nodes = [int(n / multiplier) for n in dep[1] if n >= first_line_no * multiplier]
            nodes = [self._get_node_by_lineno(x) for x in nodes]
            loopcarried_deps_dict[dep[0]] = {
                'root': self._get_node_by_lineno(dep[0]),
                'dependencies': nodes,
            }

        return loopcarried_deps_dict

    def _get_node_by_lineno(self, lineno):
        return [instr for instr in self.kernel if instr.line_number == lineno][0]

    def get_critical_path(self):
        if nx.algorithms.dag.is_directed_acyclic_graph(self.dg):
            longest_path = nx.algorithms.dag.dag_longest_path(self.dg, weight='latency')
            return [x for x in self.kernel if x['line_number'] in longest_path]
        else:
            # split to DAG
            raise NotImplementedError('Kernel is cyclic.')

    def get_loopcarried_dependencies(self):
        if nx.algorithms.dag.is_directed_acyclic_graph(self.dg):
            return self.loopcarried_deps
        else:
            # split to DAG
            raise NotImplementedError('Kernel is cyclic.')

    def find_depending(self, instruction_form, kernel, include_write=False):
        if instruction_form.operands is None:
            return
        for dst in instruction_form.operands.destination + instruction_form.operands.src_dst:
            if 'register' in dst:
                # Check for read of register until overwrite
                for instr_form in kernel:
                    if self.is_read(dst.register, instr_form):
                        yield instr_form
                        if self.is_written(dst.register, instr_form):
                            # operand in src_dst list
                            if include_write:
                                yield instr_form
                            break
                    elif self.is_written(dst.register, instr_form):
                        if include_write:
                            yield instr_form
                        break
            elif 'memory' in dst:
                # Check if base register is altered during memory access
                if 'pre_indexed' in dst.memory or 'post_indexed' in dst.memory:
                    # Check for read of base register until overwrite
                    for instr_form in kernel:
                        if self.is_read(dst.memory.base, instr_form):
                            yield instr_form
                            if self.is_written(dst.memory.base, instr_form):
                                # operand in src_dst list
                                if include_write:
                                    yield instr_form
                                break
                        elif self.is_written(dst.memory.base, instr_form):
                            if include_write:
                                yield instr_form
                            break

    def get_dependent_instruction_forms(self, instr_form=None, line_number=None):
        """
        Returns iterator
        """
        if not instr_form and not line_number:
            raise ValueError('Either instruction form or line_number required.')
        line_number = line_number if line_number else instr_form['line_number']
        if self.dg.has_node(line_number):
            return self.dg.successors(line_number)
        return iter([])

    def is_read(self, register, instruction_form):
        is_read = False
        if instruction_form.operands is None:
            return is_read
        for src in instruction_form.operands.source + instruction_form.operands.src_dst:
            if 'register' in src:
                is_read = self.parser.is_reg_dependend_of(register, src.register) or is_read
            if 'memory' in src:
                if src.memory.base is not None:
                    is_read = self.parser.is_reg_dependend_of(register, src.memory.base) or is_read
                if src.memory.index is not None:
                    is_read = (
                        self.parser.is_reg_dependend_of(register, src.memory.index) or is_read
                    )
        # Check also if read in destination memory address
        for dst in instruction_form.operands.destination + instruction_form.operands.src_dst:
            if 'memory' in dst:
                if dst.memory.base is not None:
                    is_read = self.parser.is_reg_dependend_of(register, dst.memory.base) or is_read
                if dst.memory.index is not None:
                    is_read = (
                        self.parser.is_reg_dependend_of(register, dst.memory.index) or is_read
                    )
        return is_read

    def is_written(self, register, instruction_form):
        is_written = False
        if instruction_form.operands is None:
            return is_written
        for dst in instruction_form.operands.destination + instruction_form.operands.src_dst:
            if 'register' in dst:
                is_written = self.parser.is_reg_dependend_of(register, dst.register) or is_written
            if 'memory' in dst:
                if 'pre_indexed' in dst.memory or 'post_indexed' in dst.memory:
                    is_written = (
                        self.parser.is_reg_dependend_of(register, dst.memory.base) or is_written
                    )
        # Check also for possible pre- or post-indexing in memory addresses
        for src in instruction_form.operands.source + instruction_form.operands.src_dst:
            if 'memory' in src:
                if 'pre_indexed' in src.memory or 'post_indexed' in src.memory:
                    is_written = (
                        self.parser.is_reg_dependend_of(register, src.memory.base) or is_written
                    )
        return is_written