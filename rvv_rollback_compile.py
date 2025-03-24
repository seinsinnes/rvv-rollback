import argparse
import subprocess

import rvv_rollback
import sys

"""inputs: file to compile
        path to compiler
        path to assembler/linker
        Optional vector extension preference"""

"""def compile_file():

    check_compiler capabilities
    check_assembler capabilities

    call_compiler

    rvv_rollback.rollback_file


    call_assembler"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    #parser.add_argument("filename", help="Required filename")

    parser.add_argument("-o", "--outfile", action="store", dest="outfilename")

    parser.add_argument("-c", action="store_true", dest="nolink")

    parser.add_argument("--compiler-path", action="store", dest="compiler_path")

    parser.add_argument("--assembler-path", action="store", dest="assembler_path")

    parser.add_argument("--sysroot", action="store", dest="sysroot")

    parser.add_argument("--zve32f", action="store_true", help="Use only subset of the V extension supporting element size up to 32-bit for embedded processors")

    xtheadvectorext_parser = parser.add_mutually_exclusive_group(required=False)
    xtheadvectorext_parser.add_argument("-t", "--xtheadvectorext",
                                        dest='use_xtheadvectorext',
                                        action='store_true',
                                        help="Generate output for T-Head Vector Extension included in gcc-14")
    xtheadvectorext_parser.add_argument('--v0p7', dest='use_xtheadvectorext',
                                        action='store_false',
                                        help="Generate default output for RISC-V Vector Extension version 0.7 (v0p7)")
    parser.set_defaults(use_xtheadvectorext=False)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosity (-v, -vv, etc)")
    
    args, unknownargs = parser.parse_known_args()
    print(f"rem1: {unknownargs}")

    #ordered_unknownargs = []
    #for a in sys.argv:
    #    if a in unknownargs:
    #        ordered_unknownargs.append(a)

    for unkarg in unknownargs[::-1]:
        if unkarg.strip()[0] != "-": 
            filename = unkarg
            break

    #print(f"rem1: {ordered_unknownargs}")
    print(f"input: {filename}")
    output_arch = "rv64gc_xtheadvector" if args.use_xtheadvectorext else "rv64gcv0p7"
    if filename.rpartition(".")[-1] != "o" and filename.rpartition(".")[-1] != "a":
        as_filename = filename.rpartition(".")[0] + ".s"

        compiler_cmd = f"{args.compiler_path} --sysroot={args.sysroot}  -no-integrated-as -march=rv64gc{'_zve32f' if args.zve32f else 'v'}_zvl128b  -menable-experimental-extensions -mllvm --riscv-v-vector-bits-min=128 {' '.join(unknownargs)} -S -o {as_filename} -c"
        #--sysroot=/usr/local/share/riscv-compiler/llvm-19.1/sysroot/

        if args.verbose > 0 or True:
            print(compiler_cmd)
        subprocess.run(compiler_cmd, shell=True, check=True)

        rolledback_as_filename = rvv_rollback.rollback_file(as_filename, base_isa_version=2.0, use_xtheadvectorext=args.use_xtheadvectorext, verbosity=args.verbose)

        unknownargs.remove(filename)
        asm_cmd = f"{args.assembler_path} -march={output_arch} {' '.join(unknownargs)} {'-c' if args.nolink else ''} {rolledback_as_filename} {f'-o {args.outfilename}' if args.outfilename else ''}"
    else:
        asm_cmd = f"{args.assembler_path} -march={output_arch} {' '.join(unknownargs)} {'-c' if args.nolink else ''} {f'-o {args.outfilename}' if args.outfilename else ''}"
    if args.verbose > 0 or True:
        print(asm_cmd)
    subprocess.run(asm_cmd, shell=True, check=True)

#clang --sysroot=/usr/local/share/riscv-compiler/llvm-19.1/sysroot/ -no-integrated-as -march=rv64gcv  -menable-experimental-extensions -mllvm --riscv-v-vector-bits-min=128 -O3 -S -o reduction.s -c reduction.c

#riscv64-unknown-linux-gnu-g++ -march=rv64gcv0p7 -O3 reduction-rvv0p7.s
#OR
#riscv64-linux-gnu-gcc -O3 -march=rv64g_xtheadvector reduction-rvv0p7.s
