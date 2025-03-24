"""
RVV-rollback is a tool to translate RISC-V
assembly code with Vector Extension version 1.0
to version 0.7
"""

__author__ = "Joseph Lee - EPCC (j.lee@epcc.ed.ac.uk), Christopher Day - EPCC (c.day@epcc.ed.ac.uk)"
__version__ = "0.1.4"
__license__ = "MIT"

import argparse
import re


def replace_instruction(line, linenum, base_isa_version, use_xtheadvectorext, verbosity):
    newline = line
    line_changed = False

    if use_xtheadvectorext:
        vector_extension_tag = "_xtheadvector"
    else:
        vector_extension_tag = "_v0p7"

    v_one_attribute_list = ["_v1p0","_zve32f1p0","_zve32x1p0","_zve64d1p0","_zve64f1p0","_zve64x1p0","_zvl128b1p0","_zvl32b1p0","_zvl64b1p0"]
    v_pseven_attribute_added = False
    for attribute in v_one_attribute_list:
        if attribute in newline:
            newline = newline.replace(attribute, '')
            line_changed = True
            if not v_pseven_attribute_added:
                newline = newline.replace("\"\n", f"{vector_extension_tag}\"\n")
                v_pseven_attribute_added = True


    if base_isa_version < 2.0:
        base_v2_attribute_list = ["_zicsr2p0", "_zifencei2p0"]
        for attribute in base_v2_attribute_list:
            if attribute in newline:
                newline = newline.replace(attribute, '')
                line_changed = True
    

    opcode_name_change_dict = {
        # V1.0 -> V0.7
        "vle32.v"    : "vlw.v",
        "vle16.v"    : "vlh.v",
        "vle8.v"     : "vlb.v",
        "vse32.v"    : "vsw.v",
        "vse16.v"    : "vsh.v",
        "vse8.v"     : "vsb.v",
        "vluxei32.v" : "vlxw.v",
        "vluxei16.v" : "vlxh.v",
        "vluxei8.v"  : "vlxb.v",
        "vsuxei32.v" : "vsuxw.v",
        "vsuxei16.v" : "vsuxh.v",
        "vsuxei8.v"  : "vsuxb.v",
        "vlse32.v"   : "vlsw.v",
        "vlse16.v"   : "vlsh.v",
        "vlse8.v"    : "vlsb.v",
        "vsse32.v"   : "vssw.v",
        "vsse16.v"   : "vssh.v",
        "vsse8.v"    : "vssb.v",
        "vloxei32.v" : "vlxw.v",
        "vloxei16.v" : "vlxh.v",
        "vloxei8.v"  : "vlxb.v",
        "vsoxei32.v" : "vsxw.v",
        "vsoxei16.v" : "vsxh.v",
        "vsoxei8.v"  : "vsxb.v",
        "vloxseg1e8.v" "vlxseg1b.v"
        "vluxseg1e8.v" "vlxseg1b.v"
        "vsoxseg1e8.v" "vsxseg1b.v"
        "vsuxseg1e8.v" "vsxseg1b.v"
        "vfncvt.xu.f.w": "vfncvt.xu.f.v",
        "vfncvt.x.f.w": "vfncvt.x.f.v",
        "vfncvt.f.xu.w": "vfncvt.f.xu.v",
        "vfncvt.f.x.w": "vfncvt.f.x.v",
        "vfncvt.f.f.w": "vfncvt.f.f.v",
        "vfredusum": "vfredsum",
        "vfwredusum.vs":"vfwredsum.vs",
        "vnclip.wv": "vnclip.vv",
        "vnclip.wx": "vnclip.vx",
        "vnclip.wi": "vnclip.vi",
        "vnclipu.wv": "vnclipu.vv",
        "vnclipu.wx": "vnclipu.vx",
        "vnclipu.wi": "vnclipu.vi",
        "vnsra.wv" : "vnsra.vv",
        "vnsra.wx" : "vnsra.vx",
        "vnsra.wi" : "vnsra.vi",
        "vnsrl.wv" : "vnsrl.vv",
        "vnsrl.wx" : "vnsrl.vx",
        "vnsrl.wi" : "vnsrl.vi",
        "vmandn.mm" : "vmandnot.mm",
        "vmorn.mm" : "vmornot.mm",
        "vmmv.m" : "vmcpy.m",
        "vcpopc.m" : "vmpopc.m",
        "vpopc.m" : "vmpopc.m",
        "vfirst.m" : "vmfirst.m",
    }

    for key in opcode_name_change_dict:
        if (line.__contains__(key)):
            line_changed = True
            newline = line.replace(key, opcode_name_change_dict[key])

        
    
    
    whole_register_list = ["vl1r.v", "vl1re8.v", "vl1re16.v", "vl1re32", "vl1re64",
                           "vl2r.v", "vl2re8.v", "vl2re16.v", "vl2re32", "vl2re64",
                           "vl4r.v", "vl4re8.v", "vl4re16.v", "vl4re32", "vl4re64",
                           "vl8r.v", "vl8re8.v", "vl8re16.v", "vl8re32", "vl8re64",
                           "vs1r.v", "vs2r.v","vs4r.v", "vs8r.v", 
                           "vmv1r.v", "vmv2r.v", "vmv4r.v", "vmv8r.v"]

    # WHOLE REGISTER LOAD/STORE/COPY:
    if any(word in line for word in whole_register_list):
        line_changed = True
        instruction = re.split(r"[, \t]+", line.lstrip())
        rd = instruction[1]
        rs = instruction[2]
        if (len(instruction) <= 3):
            vm = ""
        elif (instruction[3].strip("# ")):
            vm = "," + instruction[3]
        else:
            vm = ""
        newline = "# Replacing Line: {LINENUM} - {LINE}".format(
                    LINENUM=linenum, LINE=line)
        newline += "\tsd     t0, 0(sp)\n"
        newline += "\tsd     t1, 8(sp)\n"
        newline += "\tcsrr     t0, vl\n"
        newline += "\tcsrr     t1, vtype\n"
        temp_vset = ""
        temp_vinstr = ""
        print(f"VM: {vm}")
        match instruction[0]:
            case 'vl1r.v' | 'vl1re8.v' | 'vl1re16.v' | 'vl1re32' | 'vl1re64':
                temp_vset ="\tvsetvli  x0, x0, e32, m1\n"
                temp_vinstr = "\tvlw.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vl2r.v' | 'vl2re8.v' | 'vl2re16.v' | 'vl2re32' | 'vl2re64':
                temp_vset ="\tvsetvli  x0, x0, e32, m2\n"
                temp_vinstr = "\tvlw.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vl4r.v' | 'vl4re8.v' | 'vl4re16.v' | 'vl4re32' | 'vl4re64':
                temp_vset ="\tvsetvli  x0, x0, e32, m4\n"
                temp_vinstr = "\tvlw.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vl8r.v' | 'vl8re8.v' | 'vl8re16.v' | 'vl8re32' | 'vl8re64':
                temp_vset ="\tvsetvli  x0, x0, e32, m8\n"
                temp_vinstr = "\tvlw.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vs1r.v':
                temp_vset ="\tvsetvli  x0, x0, e32, m1\n"
                temp_vinstr = "\tvsw.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vs2r.v':
                temp_vset ="\tvsetvli  x0, x0, e32, m2\n"
                temp_vinstr = "\tvsw.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vs4r.v':
                temp_vset ="\tvsetvli  x0, x0, e32, m4\n"
                temp_vinstr = "\tvsw.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vs8r.v':
                temp_vset ="\tvsetvli  x0, x0, e32, m8\n"
                temp_vinstr = "\tvsw.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vmv1r.v':
                temp_vset ="\tvsetvli  x0, x0, e32, m1\n"
                temp_vinstr = "\tvmv.v.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vmv2r.v':
                temp_vset ="\tvsetvli  x0, x0, e32, m2\n"
                temp_vinstr = "\tvmv.v.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vmv4r.v':
                temp_vset ="\tvsetvli  x0, x0, e32, m4\n"
                temp_vinstr = "\tvmv.v.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
            case 'vmv8r.v':
                temp_vset ="\tvsetvli  x0, x0, e32, m8\n"
                temp_vinstr = "\tvmv.v.v    {RD}, {RS} {VM}\n".format(
                    RD=rd, RS=rs, VM=vm)
        newline += temp_vset
        newline += temp_vinstr
        newline += "\tvsetvl   x0, t0, t1\n"
        newline += "\tld     t0, 0(sp)\n"
        newline += "\tld     t1, 8(sp)\n"

        suggestion = "# Replacing Line: {LINENUM} - {LINE}\n".format(
            LINENUM=linenum, LINE=line)
        suggestion += "# Suggestion\n"
        suggestion += "# Pick 2 unused register e.g. t0, t1\n"
        suggestion += "#\tcsrr     t0, vl\t\t(may be unnecessary) \n"
        suggestion += "#\tcsrr     t1, vtype\t\t(may be unnecessary) \n"
        suggestion += "#"+temp_vset
        suggestion += "#"+temp_vinstr
        suggestion += "#\tvsetvl   x0, t0, t1\t\t(may be unnecessary) \n"
        newline += suggestion

        print("WARNING: replaced Line {LINENUM} : {LINE}".format(
            LINENUM=linenum, LINE=line))
        print("WARNING: Add -v to see suggestion (Also in output file)")

    change_instruction_list = ["vsetvl", "vsetvli", "vsetivli",
                               "vzext.vf2", "vzext.vf4", "vzext.vf8",
                               "vsext.vf2", "vsext.vf4", "vsext.vf8",
                               "csrr"]
    # Change other miscellaneous instruction
    if any(word in line for word in change_instruction_list):
        line_changed = True
        instruction = re.split(r"[, \t]+", line.strip())
        

        match instruction[0]:
            # ===========================================================
            # VECTOR CONFIGURATION
            case "vsetvl":
                # disable tail/mask agnostic policy
                newline = line.replace(", ta", "").replace(", tu", "").replace(", ma", "").replace(", mu", "")
            case "vsetvli":
                # disable tail/mask agnostic policy
                newline = line.replace(", ta", "").replace(", tu", "").replace(", ma", "").replace(", mu", "")
                fractional_LMUL = ["mf2", "mf4", "mf8"]
                if any(fLMUL in line for fLMUL in fractional_LMUL):
                    print(
                        "ERROR: Line number: {LINENUM} - Fractional LMUL".format(LINENUM=linenum))
            case 'vsetivli':  
                fractional_LMUL = ["mf2", "mf4", "mf8"]
                if any(fLMUL in line for fLMUL in fractional_LMUL):
                    print(
                        "ERROR: Line number: {LINENUM} - Fractional LMUL".format(LINENUM=linenum))
                AVL = instruction[2]
                print(f"vsetivli replacing: {line} {instruction}")
                newline = "# Replacing Line: {LINENUM} - {LINE}".format(
                    LINENUM=linenum, LINE=line)
                newline +=  "\tsd     t0, 0(sp)\t  # rvv-rollback\n"
                
                #If AVL is a bare integer it needs to be the third operand.
                if AVL.lstrip("-").isdigit():
                    newline += "\taddi   t0, x0, " + AVL +  " # rvv-rollback\n"
                else:
                    newline += "\taddi   t0, " + AVL +  " # rvv-rollback\n"
                temp =line.replace(", ta", "").replace(
                    ", tu", "").replace(", ma", "").replace(", mu", "").replace("vsetivli", "vsetvli").replace("\n","")
                temp = re.sub(r'([\s\,]+)' + AVL + r'([\s\,]+|$)', r'\1t0\2', temp)
                newline += temp + " # rvv-rollback\n"
                newline += "\tld     t0, 0(sp)\t  # rvv-rollback\n"
                suggestion = "# Replacing Line: {LINENUM} - {LINE}".format(
                    LINENUM=linenum, LINE=line)
                suggestion += "# Suggestion\n"
                suggestion += "# Pick unused register e.g. t0\n"
                suggestion += "#\taddi   t0, " + AVL + '\n'
                suggestion += "# " + temp + '\n'
                newline += suggestion

                print("WARNING: replaced Line {LINENUM} : {LINE}".format(LINENUM=linenum, LINE=line))
                print("WARNING: Add -v to see suggestion (Also in output file)")


            # ===========================================================

            # VECTOR INTEGER ZERO/SIGN EXTENSION
            case 'vzext.vf2':  # zero extend vzext.v vd, vs2, vm
                vd = instruction[1]
                vs2 = instruction[2]
                if len(instruction) > 3 and instruction[3]:
                    vm = "," + instruction[3]
                else:
                    vm = ""
                newline = "\tvwaddu.vx {VD}, {VS2}, x0 {VM}\n" # unsigned widening add zero
                newline = newline.format(VD=vd, VS2=vs2, VM=vm)

            case 'vzext.vf4':
                vd = instruction[1]
                vs2 = instruction[2]
                
                if len(instruction) > 3 and instruction[3]:
                    vm = instruction[3]
                else:
                    vm = ""
                newline = ("\tvwaddu.vx {VD}, {VS2}, x0 {VM}\n" +
                        "\tvwaddu.vx {VD}, {VD},  x0 {VM}\n")  # unsigned widening add zero twice
                newline = newline.format(VD=vd, VS2=vs2, VM=vm)
            case 'vzext.vf8':
                vd = instruction[1]
                vs2 = instruction[2]
                if instruction[3]:
                    vm = instruction[3]
                else:
                    vm = ""
                newline = ("\tvwaddu.vx {VD}, {VS2}, x0 {VM}\n" +
                        "\tvwaddu.vx {VD}, {VD},  x0 {VM}\n" +
                        "\tvwaddu.vx {VD}, {VD},  x0 {VM}\n")  # unsigned widening add zero three times
                newline = newline.format(VD=vd, VS2=vs2, VM=vm)

            case 'vsext.vf2':  # sign extend vsext.v vd, vs2, vm
                vd = instruction[1]
                vs2 = instruction[2]
                if instruction[3]:
                    vm = instruction[3]
                else:
                    vm = ""
                newline = "\tvwadd.vx {VD}, {VS2}, x0 {VM}\n"  # signed widening add zero
                newline = newline.format(VD=vd, VS2=vs2, VM=vm)

            case 'vsext.vf4':
                vd = instruction[1]
                vs2 = instruction[2]
                if instruction[3]:
                    vm = instruction[3]
                else:
                    vm = ""
                newline = ("\tvwadd.vx {VD}, {VS2}, x0 {VM}\n" +
                        "\tvwadd.vx {VD}, {VD}, x0 {VM}\n")  # signed widening add zero twice
                newline = newline.format(VD=vd, VS2=vs2, VM=vm)
            case 'vsext.vf8':
                vd = instruction[1]
                vs2 = instruction[2]
                if instruction[3]:
                    vm = instruction[3]
                else:
                    vm = ""
                newline = ("\tvwadd.vx {VD}, {VS2}, x0 {VM}\n" +
                        "\tvwadd.vx {VD}, {VD},  x0 {VM}\n" +
                        "\tvwadd.vx {VD}, {VD},  x0 {VM}\n")  # signed widening add zero three times
                newline = newline.format(VD=vd, VS2=vs2, VM=vm)
            case 'csrr':
                if instruction[2].strip() == "vlenb":
                    vd = instruction[1]
                    newline = ("\tcsrr {VD}, vl\n" +
                               "\tsrli {VD}, {VD}, 3\n")
                    newline = newline.format(VD=vd)
                else:
                    line_changed = False


    if verbosity > 0 and line_changed == True:
        print("Line number: {LINENUM}".format(LINENUM=linenum))
        print("original = " + line)
        print("updated  = " + newline)
        print("=========================================================")

    if use_xtheadvectorext:
        newline = re.sub(r'(^[#\s]*)(v[a-zA-Z0-9\.]*)', r'\1th.\2', newline, flags=re.MULTILINE)
    

    return newline
        





def rollback_file(filename, outfilename="", base_isa_version=1.0, use_xtheadvectorext=False, verbosity=0 ):
    
    if not outfilename:
        if use_xtheadvectorext:
            outfilename = filename.replace(".s", "-rvxtheadvector.s")
        else:
            outfilename = filename.replace(".s", "-rvv0p7.s")

    print("input file = {IN}  |  output file = {OUT}\n".format(IN=filename, OUT=outfilename))

    print("base ISA version = {}".format(base_isa_version))

    file = open(filename, 'r')
    outfile = open(outfilename, 'w')

    linenum = 0
    for line in file.readlines():
        linenum = linenum + 1
        newline = replace_instruction(line, linenum, base_isa_version, use_xtheadvectorext, verbosity)
        outfile.writelines(newline)


    file.close()
    outfile.close()

    return outfilename








if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("filename", help="Required filename")

    parser.add_argument("-o", "--outfile", action="store", dest="outfilename")

    # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosity (-v, -vv, etc)")

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    # Specify base ISA version to support
    parser.add_argument("-b", "--base_isa_version", action="store",
                        dest="base_isa_version", default=1.0, type=float,
                        help="RISC-V ISA version to support")
    
    
    xtheadvectorext_parser = parser.add_mutually_exclusive_group(required=False)
    xtheadvectorext_parser.add_argument("-t", "--xtheadvectorext",
                                        dest='use_xtheadvectorext',
                                        action='store_true',
                                        help="Generate output for T-Head Vector Extension included in gcc-14")
    xtheadvectorext_parser.add_argument('--v0p7', dest='use_xtheadvectorext',
                                        action='store_false',
                                        help="Generate default output for RISC-V Vector Extension version 0.7 (v0p7)")
    parser.set_defaults(use_xtheadvectorext=False)

    args = parser.parse_args()
    rollback_file(args.filename, args.outfilename, args.base_isa_version, args.use_xtheadvectorext, args.verbose )
