.text

# EXEMPLO 1: retorna uma constante
.globl exemplo1
exemplo1:
    pushq %rbp
    movq %rsp, %rbp
    subq $32, %rsp

    movl $100, %eax

    leave
    ret

# EXEMPLO 2: f(x) = x + 1
.globl exemplo2
exemplo2:
    pushq %rbp
    movq %rsp, %rbp
    subq $32, %rsp

    movl %edi, -4(%rbp)       # salva p0
    movl -4(%rbp), %eax
    addl $1, %eax
    movl %eax, -8(%rbp)       # salva v0

    movl -8(%rbp), %eax
    leave
    ret

# EXEMPLO 3: fatorial
.globl exemplo3
exemplo3:
.Lfatorial:
    pushq %rbp
    movq %rsp, %rbp
    subq $32, %rsp

    movl %edi, -4(%rbp)       # salva p0

    # zret p0 $1: se p0 == 0, retorna 1
    cmpl $0, -4(%rbp)
    jne .Lfatorial_rec
    movl $1, %eax
    leave
    ret

.Lfatorial_rec:
    # v0 = p0 + $0
    movl -4(%rbp), %eax
    addl $0, %eax
    movl %eax, -8(%rbp)

    # v1 = v0 - $1
    movl -8(%rbp), %eax
    subl $1, %eax
    movl %eax, -12(%rbp)

    # v1 = call 0 v1 (chamada recursiva à função 0)
    movl -12(%rbp), %edi
    call .Lfatorial
    movl %eax, -12(%rbp)

    # v0 = v0 * v1
    movl -8(%rbp), %eax
    imull -12(%rbp), %eax
    movl %eax, -8(%rbp)

    # ret v0
    movl -8(%rbp), %eax
    leave
    ret

# EXEMPLO 4: soma dos quadrados de 1 até p0
# Primeira funcao (funcao 0): calcula o quadrado
.globl exemplo4_quadrado
exemplo4_quadrado:
.Lquadrado:
    pushq %rbp
    movq %rsp, %rbp
    subq $32, %rsp

    movl %edi, -4(%rbp)       # salva p0

    # v0 = p0 * p0
    movl -4(%rbp), %eax
    imull -4(%rbp), %eax
    movl %eax, -8(%rbp)

    # ret v0
    movl -8(%rbp), %eax
    leave
    ret

# Segunda funcao (funcao 1): soma recursivamente os quadrados
.globl exemplo4_soma
exemplo4_soma:
.Lsoma_quadrados:
    pushq %rbp
    movq %rsp, %rbp
    subq $32, %rsp

    movl %edi, -4(%rbp)       # salva p0 desta chamada

    # zret p0 $0: se p0 == 0, retorna 0
    cmpl $0, -4(%rbp)
    jne .Lsoma_rec
    movl $0, %eax
    leave
    ret

.Lsoma_rec:
    # v0 = p0 - $1
    movl -4(%rbp), %eax
    subl $1, %eax
    movl %eax, -8(%rbp)

    # v1 = call 0 p0: calcula p0 * p0
    movl -4(%rbp), %edi
    call .Lquadrado
    movl %eax, -12(%rbp)

    # v0 = call 1 v0: soma_quadrados(p0 - 1)
    movl -8(%rbp), %edi
    call .Lsoma_quadrados
    movl %eax, -8(%rbp)

    # v0 = v0 + v1
    movl -8(%rbp), %eax
    addl -12(%rbp), %eax
    movl %eax, -8(%rbp)

    # ret v0
    movl -8(%rbp), %eax
    leave
    ret
