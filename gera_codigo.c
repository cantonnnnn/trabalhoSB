/* Eduardo Canton Ferreira e Silva 2410837 3WC */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "gera_codigo.h"

/* Operando: tipo = 'v' (variavel local), 'p' (parametro p0) ou '$' (constante) */
typedef struct {
    char tipo;
    int val;
} Operando;

static void emit(unsigned char code[], int *i, int b)
{
    code[(*i)++] = (unsigned char)(b & 0xFF);
}

static void emit_imm(unsigned char code[], int *i, int v)
{
    emit(code, i, v);
    emit(code, i, v >> 8);
    emit(code, i, v >> 16);
    emit(code, i, v >> 24);
}

/* "v3" -> {'v',3}   "p0" -> {'p',0}   "$-10" -> {'$',-10} */
static Operando le_op(const char *s)
{
    Operando o = {0, 0};
    sscanf(s, "%c%d", &o.tipo, &o.val);
    return o;
}

/* deslocamento em relacao a %rbp: p0 em -4, vN em -8-4*N */
static int desloc(Operando o)
{
    return (o.tipo == 'p') ? -4 : -8 - 4 * o.val;
}

static void prologo(unsigned char code[], int *i)
{
    emit(code, i, 0x55);                                  /* push %rbp */
    emit(code, i, 0x48); emit(code, i, 0x89); emit(code, i, 0xE5);   /* mov %rsp,%rbp */
    emit(code, i, 0x48); emit(code, i, 0x83); emit(code, i, 0xEC); emit(code, i, 0x20); /* sub $0x20,%rsp */
    emit(code, i, 0x89); emit(code, i, 0x7D); emit(code, i, 0xFC);   /* mov %edi,-4(%rbp): salva p0 */
}

static void epilogo(unsigned char code[], int *i)
{
    emit(code, i, 0xC9);                                  /* leave */
    emit(code, i, 0xC3);                                  /* ret */
}

/* %eax <- operando */
static void carrega_eax(unsigned char code[], int *i, Operando o)
{
    if (o.tipo == '$') {
        emit(code, i, 0xB8);                              /* mov $imm,%eax */
        emit_imm(code, i, o.val);
    } else {
        emit(code, i, 0x8B); emit(code, i, 0x45); emit(code, i, desloc(o)); /* mov d(%rbp),%eax */
    }
}

/* %eax <- %eax op operando */
static void aplica_op(unsigned char code[], int *i, char op, Operando o)
{
    if (o.tipo == '$') {
        if (op == '+')      emit(code, i, 0x05);          /* add $imm,%eax */
        else if (op == '-') emit(code, i, 0x2D);          /* sub $imm,%eax */
        else { emit(code, i, 0x69); emit(code, i, 0xC0); } /* imul $imm,%eax,%eax */
        emit_imm(code, i, o.val);
    } else {
        if (op == '+')      emit(code, i, 0x03);          /* add d(%rbp),%eax */
        else if (op == '-') emit(code, i, 0x2B);          /* sub d(%rbp),%eax */
        else { emit(code, i, 0x0F); emit(code, i, 0xAF); } /* imul d(%rbp),%eax */
        emit(code, i, 0x45);
        emit(code, i, desloc(o));
    }
}

/* d(%rbp) <- %eax, para a variavel vN */
static void guarda_var(unsigned char code[], int *i, int var)
{
    emit(code, i, 0x89); emit(code, i, 0x45); emit(code, i, -8 - 4 * var);
}

void gera_codigo(FILE *f, unsigned char code[], funcp *entry)
{
    char linha[100];
    char comando[20];
    char a[20], b[20], op;
    int i = 0;                  /* proxima posicao livre em code */
    int function_start[50];     /* inicio de cada funcao LBS */
    int num_functions = 0;
    int var, num_func, salto;

    *entry = NULL;
    while (fgets(linha, sizeof(linha), f) != NULL)
    {
        if (sscanf(linha, "%19s", comando) != 1)
            continue;

        if (strcmp(comando, "function") == 0)
        {
            function_start[num_functions++] = i;
            *entry = (funcp) &code[i];
            prologo(code, &i);
        }
        else if (strcmp(comando, "end") == 0)
        {
            /* o epilogo ja foi gerado pelo ret */
        }
        else if (strcmp(comando, "ret") == 0)
        {
            sscanf(linha, "ret %19s", a);
            carrega_eax(code, &i, le_op(a));
            epilogo(code, &i);
        }
        else if (strcmp(comando, "zret") == 0)
        {
            sscanf(linha, "zret %19s %19s", a, b);
            carrega_eax(code, &i, le_op(a));
            emit(code, &i, 0x83); emit(code, &i, 0xF8); emit(code, &i, 0x00); /* cmp $0,%eax */
            emit(code, &i, 0x75);                                             /* jne */
            salto = i;
            emit(code, &i, 0x00);
            carrega_eax(code, &i, le_op(b));
            epilogo(code, &i);
            code[salto] = (unsigned char)(i - (salto + 1));
        }
        else if (sscanf(linha, "v%d = call %d %19s", &var, &num_func, a) == 3)
        {
            Operando o = le_op(a);
            if (o.tipo == '$') {
                emit(code, &i, 0xBF);                                         /* mov $imm,%edi */
                emit_imm(code, &i, o.val);
            } else {
                emit(code, &i, 0x8B); emit(code, &i, 0x7D); emit(code, &i, desloc(o)); /* mov d(%rbp),%edi */
            }
            emit(code, &i, 0xE8);                                             /* call rel32 */
            emit_imm(code, &i, function_start[num_func] - (i + 4));
            guarda_var(code, &i, var);
        }
        else if (sscanf(linha, "v%d = %19s %c %19s", &var, a, &op, b) == 4)
        {
            carrega_eax(code, &i, le_op(a));
            aplica_op(code, &i, op, le_op(b));
            guarda_var(code, &i, var);
        }
    }
}
