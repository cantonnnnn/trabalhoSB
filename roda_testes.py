#!/usr/bin/env python3
"""
Suite de testes para o gerador de codigo LBS (INF1018).

Uso (na pasta que contem gera_codigo.c, gera_codigo.h, main_teste.c e este arquivo):
    python3 roda_testes.py            # compila, gera testes/*.lbs e roda tudo
    python3 roda_testes.py -v         # mostra tambem os testes que passaram, com detalhes
    python3 roda_testes.py -k fat     # roda so os testes cujo nome contem "fat"
    python3 roda_testes.py --sem-compilar

Cada teste: programa LBS + lista de argumentos. O resultado esperado vem de um
interpretador de referencia (inteiros de 32 bits com sinal, com overflow "dando a volta").
"""
import os, subprocess, sys
sys.setrecursionlimit(200000)

# ---------------------------------------------------------------- interpretador
def wrap(x):
    x &= 0xFFFFFFFF
    return x - (1 << 32) if x >= (1 << 31) else x

def parse(src):
    funcs, cur = [], None
    for ln in src.strip().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if ln == "function":
            cur = []
        elif ln == "end":
            funcs.append(cur); cur = None
        else:
            cur.append(ln.split())
    return funcs

def run(funcs, n, p):
    loc = {}
    def val(t):
        if t == "p0": return p
        if t[0] == "v": return loc[int(t[1:])]
        return wrap(int(t[1:]))
    for c in funcs[n]:
        if c[0] == "ret":
            return val(c[1])
        if c[0] == "zret":
            if val(c[1]) == 0:
                return val(c[2])
            continue
        v = int(c[0][1:])             # atribuicao: vN = ...
        if c[2] == "call":
            loc[v] = run(funcs, int(c[3]), val(c[4]))
        else:
            a, op, b = val(c[2]), c[3], val(c[4])
            loc[v] = wrap(a + b if op == "+" else a - b if op == "-" else a * b)
    raise RuntimeError("funcao sem ret")

def esperado(src, args):
    f = parse(src)
    return [run(f, len(f) - 1, wrap(a)) for a in args]

# ---------------------------------------------------------------- testes
T = []          # (nome, fonte, args, opcoes)
def t(nome, src, args=(0, 1, -1, 7, 100), **opt):
    T.append((nome, src, list(args), opt))

BIG = 2147483647
SMALL = (0, 1, -1, 7, -7, 100)

# ---- 1. exemplos do enunciado
t("enunciado_1_ret_constante", "function\nret $100\nend")
t("enunciado_2_x_mais_1", "function\nv0 = p0 + $1\nret v0\nend", (0, 1, -1, 5, 41, -100, BIG))
t("enunciado_3_fatorial", """function
zret p0 $1
v0 = p0 + $0
v1 = v0 - $1
v1 = call 0 v1
v0 = v0 * v1
ret v0
end""", (0, 1, 2, 3, 5, 10, 12))
t("enunciado_4_soma_quadrados", """function
v0 = p0 * p0
ret v0
end
function
zret p0 $0
v0 = p0 - $1
v1 = call 0 p0
v0 = call 1 v0
v0 = v0 + v1
ret v0
end""", (0, 1, 2, 3, 10, 50, 100))

# ---- 2. retornos simples
t("ret_p0", "function\nret p0\nend", (0, 5, -5, BIG, -BIG - 1))
t("ret_constante_zero", "function\nret $0\nend")
t("ret_constante_negativa", "function\nret $-42\nend")
t("ret_constante_grande", "function\nret $2147483647\nend")
t("ret_constante_minima", "function\nret $-2147483648\nend")
t("ret_constante_com_mais", "function\nret $+5\nend")
t("ret_variavel", "function\nv0 = p0 + $0\nret v0\nend", SMALL)
t("ret_ignora_codigo_depois", "function\nret $1\nv0 = p0 + $1\nret v0\nend")

# ---- 3. operacoes basicas (const/param/var)
t("soma_const_const", "function\nv0 = $3 + $4\nret v0\nend")
t("sub_const_const", "function\nv0 = $3 - $10\nret v0\nend")
t("mul_const_const", "function\nv0 = $-6 * $7\nret v0\nend")
t("soma_p0_p0", "function\nv0 = p0 + p0\nret v0\nend", SMALL)
t("sub_p0_p0", "function\nv0 = p0 - p0\nret v0\nend", SMALL)
t("mul_p0_p0", "function\nv0 = p0 * p0\nret v0\nend", SMALL + (46341, -46341))
t("const_menos_p0", "function\nv0 = $10 - p0\nret v0\nend", SMALL)
t("p0_menos_const", "function\nv0 = p0 - $10\nret v0\nend", SMALL)
t("mul_por_zero", "function\nv0 = p0 * $0\nret v0\nend", SMALL)
t("mul_por_um", "function\nv0 = p0 * $1\nret v0\nend", SMALL)
t("mul_por_menos_um", "function\nv0 = p0 * $-1\nret v0\nend", SMALL)
t("soma_zero", "function\nv0 = p0 + $0\nret v0\nend", SMALL)

# ---- 4. fronteira imm8 / imm32 (127, -128, 128, -129)
for c in (127, 128, -128, -129, 255, 256, 32767, 65536, BIG, -BIG - 1):
    for op, nome in (("+", "soma"), ("-", "sub"), ("*", "mul")):
        t(f"imm_{nome}_{c}", f"function\nv0 = p0 {op} ${c}\nret v0\nend", (0, 1, -1, 3, -3, 1000))

# ---- 5. overflow (dar a volta em 32 bits)
t("overflow_soma", "function\nv0 = p0 + $2147483647\nret v0\nend", (1, 2, BIG, -1))
t("overflow_sub", "function\nv0 = p0 - $2147483647\nret v0\nend", (-2, -3, -BIG - 1, 0))
t("overflow_mul", "function\nv0 = p0 * p0\nv0 = v0 * p0\nret v0\nend", (1000, 2000, 100000, -100000, BIG))

# ---- 6. variaveis locais
t("todas_5_variaveis", """function
v0 = p0 + $1
v1 = p0 + $2
v2 = p0 + $3
v3 = p0 + $4
v4 = p0 + $5
v0 = v0 * v1
v2 = v2 * v3
v0 = v0 + v2
v0 = v0 - v4
ret v0
end""", SMALL)
t("variaveis_independentes", """function
v0 = $11 + $0
v1 = $22 + $0
v2 = $33 + $0
v3 = $44 + $0
v4 = $55 + $0
v4 = v4 - v3
v3 = v3 - v2
v2 = v2 - v1
v1 = v1 - v0
v0 = v4 + v3
v0 = v0 + v2
v0 = v0 + v1
ret v0
end""")
for i in range(5):
    t(f"usa_somente_v{i}", f"function\nv{i} = p0 * $3\nv{i} = v{i} + $1\nret v{i}\nend", SMALL)
t("var_op_var_mesma", "function\nv0 = p0 + $0\nv0 = v0 + v0\nv0 = v0 * v0\nret v0\nend", SMALL)
t("sobrescreve_variavel", "function\nv0 = $1 + $1\nv0 = $5 + $5\nv0 = v0 - $3\nret v0\nend")
t("var_const_primeiro", "function\nv0 = p0 + $2\nv1 = $100 - v0\nret v1\nend", SMALL)
t("var_var_diferentes", "function\nv0 = p0 + $2\nv1 = p0 * $3\nv2 = v0 - v1\nv3 = v1 - v0\nv4 = v2 * v3\nret v4\nend", SMALL)
t("expressao_longa", """function
v0 = p0 * p0
v1 = v0 * p0
v2 = v1 + v0
v2 = v2 + p0
v2 = v2 + $1
ret v2
end""", SMALL)  # p^3+p^2+p+1

# ---- 7. zret
t("zret_retorna_quando_zero", "function\nzret p0 $99\nret $1\nend", (0, 1, -1, 5))
t("zret_ret_p0", "function\nzret p0 p0\nret $5\nend", (0, 1, -1, 5))
t("zret_const_zero_sempre_retorna", "function\nzret $0 $7\nret $8\nend")
t("zret_const_nao_zero_nunca_retorna", "function\nzret $5 $7\nret $8\nend")
t("zret_const_negativa_nao_retorna", "function\nzret $-1 $7\nret $8\nend")
t("zret_com_variavel", "function\nv0 = p0 - $3\nzret v0 $100\nret $200\nend", (3, 4, 2, 0))
t("zret_segundo_operando_var", "function\nv0 = p0 * $2\nzret p0 v0\nret $-1\nend", (0, 1, 5))
t("zret_encadeados", """function
zret p0 $10
v0 = p0 - $1
zret v0 $20
v0 = p0 - $2
zret v0 $30
ret $40
end""", (0, 1, 2, 3, -1))
t("zret_no_meio_e_calculo_depois", """function
v0 = p0 + $0
zret v0 $0
v0 = v0 * $2
v0 = v0 + $1
ret v0
end""", SMALL)
t("zret_apos_operacao_grande", """function
v0 = p0 * $100000
v1 = v0 * $100000
zret v1 $1
ret $2
end""", (0, 1, 5, 42949, 65536))

# ---- 8. chamadas
t("call_constante", "function\nv0 = p0 * $2\nret v0\nend\nfunction\nv0 = call 0 $21\nret v0\nend", (0, 1))
t("call_p0", "function\nv0 = p0 * $2\nret v0\nend\nfunction\nv0 = call 0 p0\nret v0\nend", SMALL)
t("call_variavel", "function\nv0 = p0 + $1\nret v0\nend\nfunction\nv1 = p0 * $3\nv2 = call 0 v1\nret v2\nend", SMALL)
t("call_resultado_na_mesma_var", "function\nv0 = p0 + $1\nret v0\nend\nfunction\nv0 = p0 + $5\nv0 = call 0 v0\nret v0\nend", SMALL)
t("call_constante_negativa", "function\nv0 = p0 * p0\nret v0\nend\nfunction\nv0 = call 0 $-9\nret v0\nend", (0,))
t("call_duas_vezes_seguidas", "function\nv0 = p0 * $2\nret v0\nend\nfunction\nv0 = call 0 p0\nv0 = call 0 v0\nret v0\nend", SMALL)
t("call_preserva_variaveis_do_chamador", """function
v0 = $1000 + $0
v1 = $2000 + $0
v2 = $3000 + $0
v3 = $4000 + $0
v4 = $5000 + $0
v0 = p0 + $1
ret v0
end
function
v0 = p0 + $10
v1 = p0 + $20
v2 = p0 + $30
v3 = p0 + $40
v4 = call 0 p0
v0 = v0 + v1
v0 = v0 + v2
v0 = v0 + v3
v0 = v0 + v4
ret v0
end""", SMALL)
t("call_preserva_parametro_do_chamador", """function
v0 = p0 * $100
ret v0
end
function
v0 = call 0 $7
v1 = v0 + p0
ret v1
end""", SMALL)
t("call_encadeada_3_funcoes", """function
v0 = p0 + $1
ret v0
end
function
v0 = call 0 p0
v0 = v0 * $2
ret v0
end
function
v0 = call 1 p0
v0 = call 0 v0
ret v0
end""", SMALL)
t("call_funcao_do_meio_nao_e_a_ultima", """function
ret $1
end
function
ret $2
end
function
v0 = call 0 p0
v1 = call 1 p0
v2 = v0 + v1
ret v2
end""", (0,))
t("call_so_a_ultima_e_o_entry", "function\nret $1\nend\nfunction\nret $2\nend\nfunction\nret $3\nend", (0,))
t("call_10_funcoes_em_cadeia", "\n".join(
    ["function\nv0 = p0 + $1\nret v0\nend"] +
    [f"function\nv0 = call {i} p0\nv0 = v0 + $1\nret v0\nend" for i in range(9)]), (0, 5, -20))
t("call_funcao_chama_varias_anteriores", """function
v0 = p0 + $1
ret v0
end
function
v0 = p0 * $2
ret v0
end
function
v0 = p0 - $3
ret v0
end
function
v0 = call 0 p0
v1 = call 1 p0
v2 = call 2 p0
v3 = v0 + v1
v3 = v3 + v2
ret v3
end""", SMALL)
t("call_usa_zret_na_callee", """function
zret p0 $100
ret p0
end
function
v0 = call 0 p0
v1 = call 0 $0
v0 = v0 + v1
ret v0
end""", SMALL)

# ---- 9. recursao
t("rec_fatorial_sem_v0", """function
zret p0 $1
v0 = p0 - $1
v0 = call 0 v0
v0 = v0 * p0
ret v0
end""", (0, 1, 2, 3, 4, 5, 6, 10, 12))
t("rec_soma_1_ate_n", """function
zret p0 $0
v0 = p0 - $1
v0 = call 0 v0
v0 = v0 + p0
ret v0
end""", (0, 1, 2, 10, 100, 1000))
t("rec_fibonacci", """function
v0 = p0 - $1
zret p0 $0
zret v0 $1
v1 = call 0 v0
v2 = p0 - $2
v2 = call 0 v2
v1 = v1 + v2
ret v1
end""", (0, 1, 2, 3, 5, 10, 15, 20))
t("rec_potencia_de_2", """function
zret p0 $1
v0 = p0 - $1
v0 = call 0 v0
v0 = v0 * $2
ret v0
end""", (0, 1, 2, 10, 20, 30, 31, 32))
t("rec_contagem_regressiva_retorna_0", """function
zret p0 $0
v0 = p0 - $1
v0 = call 0 v0
ret v0
end""", (0, 1, 5, 50, 5000))
t("rec_profunda_10000", """function
zret p0 $0
v0 = p0 - $1
v0 = call 0 v0
v0 = v0 + $1
ret v0
end""", (10000,))
t("rec_com_funcao_auxiliar", """function
v0 = p0 * p0
ret v0
end
function
zret p0 $0
v0 = p0 - $1
v1 = call 1 v0
v2 = call 0 p0
v1 = v1 + v2
ret v1
end""", (0, 1, 2, 5, 10))
t("rec_usa_todas_as_5_variaveis", """function
zret p0 $0
v0 = p0 + $1
v1 = p0 + $2
v2 = p0 + $3
v3 = p0 - $1
v4 = call 0 v3
v0 = v0 + v1
v0 = v0 + v2
v0 = v0 + v4
ret v0
end""", (0, 1, 2, 5, 20))

# ---- 10. formato de arquivo
t("arquivo_com_linha_em_branco_no_final", "function\nv0 = p0 + $1\nret v0\nend\n\n", SMALL)
t("arquivo_com_crlf", "function\nv0 = p0 * $3\nret v0\nend", SMALL, crlf=True)
t("arquivo_sem_newline_final", "function\nv0 = p0 * $3\nret v0\nend", SMALL, sem_nl=True)
t("arquivo_50_linhas", "function\n" + "v0 = p0 + $1\nv0 = v0 + $1\n" * 23 + "ret v0\nend", (0, 1, -50))

# ---- 11. matriz: operadores x tipos de operando
A = ["$7", "$-300", "p0", "v0"]
B = ["$5", "$-129", "$100000", "p0", "v0"]
for op, nome in (("+", "soma"), ("-", "sub"), ("*", "mul")):
    for a in A:
        for b in B:
            lbl = lambda s: s.replace("$-", "neg").replace("$", "c")
            t(f"matriz_{nome}_{lbl(a)}_{lbl(b)}",
              f"function\nv0 = p0 + $3\nv1 = {a} {op} {b}\nret v1\nend",
              (0, 1, -7, 123, 100000, BIG))

# ---------------------------------------------------------------- execucao
def escreve(nome, src, opt):
    os.makedirs("testes", exist_ok=True)
    txt = src.strip("\n") + "\n" if not opt.get("sem_nl") else src.strip("\n")
    if opt.get("crlf"):
        txt = txt.replace("\n", "\r\n")
    path = os.path.join("testes", nome + ".lbs")
    with open(path, "w", newline="") as f:
        f.write(txt)
    return path

def main():
    ap = sys.argv[1:]
    verboso = "-v" in ap
    filtro = ap[ap.index("-k") + 1] if "-k" in ap else None
    if "--sem-compilar" not in ap:
        cmd = ["gcc", "-Wall", "-Wa,--execstack", "-o", "prog_teste", "main_teste.c", "gera_codigo.c"]
        print("$", " ".join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True)
        warns = [l for l in r.stderr.splitlines() if "requires executable stack" not in l and l.strip()]
        if r.returncode != 0:
            print(r.stderr); print("NAO COMPILOU (grau zero no trabalho!)"); sys.exit(1)
        if warns:
            print("AVISOS DO COMPILADOR:"); print("\n".join(warns))
    ok = falhas = 0
    for nome, src, args, opt in T:
        if filtro and filtro not in nome:
            continue
        path = escreve(nome, src, opt)
        esp = esperado(src, args)
        try:
            p = subprocess.run(["./prog_teste", path] + [str(a) for a in args],
                               capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            print(f"FALHOU  {nome}: TIMEOUT (loop infinito?)"); falhas += 1; continue
        if p.returncode < 0:
            print(f"FALHOU  {nome}: CRASH (sinal {-p.returncode}; 11 = segfault)"); falhas += 1; continue
        obtido = p.stdout.split()
        if obtido == [str(x) for x in esp]:
            ok += 1
            if verboso:
                print(f"ok      {nome}: " + ", ".join(f"f({a})={e}" for a, e in zip(args, esp)))
        else:
            falhas += 1
            print(f"FALHOU  {nome}")
            print(f"        arquivo : {path}")
            for i, a in enumerate(args):
                o = obtido[i] if i < len(obtido) else "?"
                marca = "" if o == str(esp[i]) else "   <-- ERRO"
                print(f"        f({a}) esperado={esp[i]} obtido={o}{marca}")
    print(f"\n{ok} passaram, {falhas} falharam, de {ok + falhas} testes")
    sys.exit(1 if falhas else 0)

if __name__ == "__main__":
    main()
