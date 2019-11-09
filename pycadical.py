from cffi import FFI
import os
import threading

""" The declarations below are copied from the CaDiCaL source code licensed as:
MIT License

Copyright (c) 2016-2019 Armin Biere, Johannes Kepler University Linz, Austria

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

_ffi = FFI()
_ffi.cdef("""
// C wrapper for CaDiCaL's C++ API following IPASIR.

typedef struct CCaDiCaL CCaDiCaL;

const char * ccadical_signature (void);
CCaDiCaL * ccadical_init (void);
void ccadical_release (CCaDiCaL *);

void ccadical_add (CCaDiCaL *, int lit);
void ccadical_assume (CCaDiCaL *, int lit);
int ccadical_solve (CCaDiCaL *);
int ccadical_val (CCaDiCaL *, int lit);
int ccadical_failed (CCaDiCaL *, int lit);

void ccadical_set_terminate (CCaDiCaL *,
  void * state, int (*terminate)(void * state));

/*------------------------------------------------------------------------*/

// Non-IPASIR conformant 'C' functions.

void ccadical_set_option (CCaDiCaL *, const char * name, int val);
void ccadical_limit (CCaDiCaL *, const char * name, int limit);
int ccadical_get_option (CCaDiCaL *, const char * name);
void ccadical_print_statistics (CCaDiCaL *);
int64_t ccadical_active (CCaDiCaL *);
int64_t ccadical_irredundant (CCaDiCaL *);
int ccadical_fixed (CCaDiCaL *, int lit);
void ccadical_terminate (CCaDiCaL *);
void ccadical_freeze (CCaDiCaL *, int lit);
int ccadical_frozen (CCaDiCaL *, int lit);
void ccadical_melt (CCaDiCaL *, int lit);
int ccadical_simplify (CCaDiCaL *);

""")

try:
    _lib = _ffi.dlopen(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "libcadical.so"
        )
    )
except OSError as err:
    raise RuntimeError(
        "libcadical.so not found, run build_libcadical.sh"
    ) from err

version = _ffi.string(_lib.ccadical_signature())

_status_to_bool = {0: None, 10: True, 20: False}
_value_to_bool = {1: True, 0: None, -1: False}


class Solver:
    def __init__(self):
        self.__solver = _lib.ccadical_init()
        self.__exception = None

    def __del__(self):
        _lib.ccadical_release(self.__solver)

    def add(self, lit):
        _lib.ccadical_add(self.__solver, lit)

    def assume(self, lit):
        _lib.ccadical_assume(self.__solver, lit)

    def solve(self, interruptible=True):
        result = None

        def run_solve():
            nonlocal result
            result = _status_to_bool[_lib.ccadical_solve(self.__solver)]

        if interruptible:
            solve_thread = threading.Thread(target=run_solve)
            solve_thread.start()
            try:
                solve_thread.join()
            except BaseException:
                self.terminate()
                solve_thread.join()
                raise
        else:
            run_solve()
        return result

    def val(self, lit):
        return _lib.ccadical_val(self.__solver, lit) > 0

    def failed(self, lit):
        return bool(_lib.ccadical_failed(self.__solver, lit))

    # set_terminate not supported

    def set_option(self, option, value):
        _lib.ccadical_set_option(self.__solver, option.encode(), value)

    def limit(self, limit, value):
        _lib.ccadical_set_option(self.__solver, limit.encode(), value)

    def get_option(self, option):
        return _lib.ccadical_get_option(self.__solver, option.encode())

    def print_statistics(self):
        return _lib.ccadical_print_statistics(self.__solver)

    def active(self):
        return _lib.ccadical_active(self.__solver)

    def irredundant(self):
        return _lib.ccadical_irredundant(self.__solver)

    def fixed(self, lit):
        return _value_to_bool[_lib.ccadical_fixed(self.__solver, lit)]

    def terminate(self):
        _lib.ccadical_terminate(self.__solver)

    def freeze(self, lit):
        _lib.ccadical_freeze(self.__solver, lit)

    def frozen(self, lit):
        return bool(_lib.ccadical_frozen(self.__solver, lit))

    def melt(self, lit):
        _lib.ccadical_melt(self.__solver, lit)

    def simplify(self):
        _lib.ccadical_simplify(self.__solver)

    def add_clause(self, lits):
        for lit in lits:
            self.add(lit)
        self.add(0)


__all__ = ['Solver']
