/*Eduardo Canton 2410837 3WC*/
/*Gabriel Petillo 2521319 3WC*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "gera_codigo.h"

typedef struct  /*Operando do tipo = v(variavel local), p(parametro p0) ou $(constante)*/
{
    char tipo;
    int val;
} Operando;

static void grava_byte(unsigned char code[], int *i, int b)
{
    code[(*i)++] = (unsigned char)(b & 0xFF);
}

static void grava_int32(unsigned char code[], int *i, int v)
{
    grava_byte(code, i, v);
    grava_byte(code, i, v >> 8);
    grava_byte(code, i, v >> 16);
    grava_byte(code, i, v >> 24);
}

static Operando le_op(const char *s)    /*"v3" -> {'v',3}   "p0" -> {'p',0}   "$-10" -> {'$',-10}*/
{
    Operando o = {0, 0};
    sscanf(s, "%c%d", &o.tipo, &o.val);
    return o;
}

static int desloc(Operando o)   /*deslocamento em relacao a %rbp: p0 em -4, variavel local n em -8-4*N*/
{
    if(o.tipo == 'p')
    {
        return -4;
    }
    else
    {
        return -8 - 4 * o.val;
    }
}

static void carrega_eax(unsigned char code[], int *i, Operando o)   /*%eax <- operando*/
{
    if (o.tipo == '$')
    {
        grava_byte(code, i, 0xB8);    /*mov $const,%eax*/
        grava_int32(code, i, o.val);
    }
    else
    {
        grava_byte(code, i, 0x8B); grava_byte(code, i, 0x45); grava_byte(code, i, desloc(o)); /*mov d(%rbp),%eax*/
    }
}

static void aplica_op(unsigned char code[], int *i, char op, Operando o)    /*%eax <- (%eax) operação operando*/
{
    if (o.tipo == '$')
    {
        if (o.val >= -128 && o.val <= 127)    /*constante cabe em 1 byte com sinal*/
        {
            if (op == '+')
            {
                grava_byte(code, i, 0x83); grava_byte(code, i, 0xC0);    /*add $const8,%eax*/
            }
            else if (op == '-')
            {
                grava_byte(code, i, 0x83); grava_byte(code, i, 0xE8);    /*sub $const8,%eax*/
            }
            else
            {
                grava_byte(code, i, 0x6B); grava_byte(code, i, 0xC0);    /*imul $const8,%eax,%eax*/
            }
            grava_byte(code, i, o.val);
        }
        else
        {
            if (op == '+')
            {
                grava_byte(code, i, 0x05);    /*add $const32,%eax*/
            }
            else if (op == '-')
            {
                grava_byte(code, i, 0x2D);    /*sub $const32,%eax*/
            }
            else
            {
                grava_byte(code, i, 0x69); grava_byte(code, i, 0xC0);    /*imul $const32,%eax,%eax*/
            }
            grava_int32(code, i, o.val);
        }
    }
    else
    {
        if (op == '+')
        {
            grava_byte(code, i, 0x03);    /*add d(%rbp),%eax*/
        }
        else if (op == '-')
        {
            grava_byte(code, i, 0x2B);    /*sub d(%rbp),%eax*/
        }
        else
        {
            grava_byte(code, i, 0x0F); grava_byte(code, i, 0xAF);   /*imul d(%rbp),%eax*/
        }
        grava_byte(code, i, 0x45);
        grava_byte(code, i, desloc(o));
    }
}

static void guardaVar(unsigned char code[], int *i, int var)   /*d(%rbp) <- %eax, para a variavel vN*/
{
    grava_byte(code, i, 0x89); grava_byte(code, i, 0x45); grava_byte(code, i, -8 - 4 * var);
}

void gera_codigo(FILE *f, unsigned char code[], funcp *entry)
{
    char linha[100];
    char comando[20];
    char a[20], b[20], op;
    int i = 0;      /*proxima posicao livre em code*/
    int num_saltos = 0;
    int num_functions = 0;
    int var, num_func, salto,fim, k, p, rel;
    int saltos_fim[50];     /*posicao do rel32 de cada jmp (de ret/zret) que vai para o end*/
    int function_start[50];     /*inicio de cada funcao LBS*/
    
    *entry = NULL;
    while (fgets(linha, sizeof(linha), f) != NULL)
    {
        if (sscanf(linha, "%19s", comando) != 1)
        {
            continue;
        }
        if (comando[0] == 'f')
        {
            function_start[num_functions++] = i;
            num_saltos = 0;
            *entry = (funcp) &code[i];
            grava_byte(code, &i, 0x55);    /*push %rbp*/
            grava_byte(code, &i, 0x48); grava_byte(code, &i, 0x89); grava_byte(code, &i, 0xE5);  /*mov %rsp,%rbp*/
            grava_byte(code, &i, 0x48); grava_byte(code, &i, 0x83); grava_byte(code, &i, 0xEC); grava_byte(code, &i, 0x20); /*sub $0x20,%rsp*/
            grava_byte(code, &i, 0x89); grava_byte(code, &i, 0x7D); grava_byte(code, &i, 0xFC);  /*mov %edi,-4(%rbp): salva p0*/
        }
        else if (comando[0] == 'e')
        {
            fim = i;                       /*aqui comeca o leave; ret desta funcao*/
            grava_byte(code, &i, 0xC9);    /*leave*/
            grava_byte(code, &i, 0xC3);    /*ret*/
            for (k = 0; k < num_saltos; k++)    /*preenche quaisquer jmp de ret/zret*/
            {
                p = saltos_fim[k];
                rel = fim - (p + 4);       /*destino - endereco da proxima instrucao*/
                grava_int32(code, &p, rel);
            }
        }
        else if (comando[0] == 'r')
        {
            sscanf(linha, "ret %19s", a);
            carrega_eax(code, &i, le_op(a));
            grava_byte(code, &i, 0xE9);    /*jmp rel32 (para o end)*/
            saltos_fim[num_saltos++] = i;
            grava_int32(code, &i, 0);      /*provisorio: preenchido no end*/
        }
        else if (comando[0] == 'z')
        {
            sscanf(linha, "zret %19s %19s", a, b);
            carrega_eax(code, &i, le_op(a));
            grava_byte(code, &i, 0x83); grava_byte(code, &i, 0xF8); grava_byte(code, &i, 0x00);   /*cmp $0,%eax*/
            grava_byte(code, &i, 0x75);   /*jne*/
            salto = i;
            grava_byte(code, &i, 0x00);
            carrega_eax(code, &i, le_op(b));
            grava_byte(code, &i, 0xE9);    /*jmp rel32 (para o end)*/
            saltos_fim[num_saltos++] = i;
            grava_int32(code, &i, 0);      /*provisorio: preenchido no end*/
            code[salto] = (unsigned char)(i - (salto + 1));
        }
        else if (sscanf(linha, "v%d = call %d %19s", &var, &num_func, a) == 3)
        {
            Operando o = le_op(a);
            if (o.tipo == '$')
            {
                grava_byte(code, &i, 0xBF);   /*mov $const,%edi*/
                grava_int32(code, &i, o.val);
            }
            else
            {
                grava_byte(code, &i, 0x8B); grava_byte(code, &i, 0x7D); grava_byte(code, &i, desloc(o));  /*mov d(%rbp),%edi*/
            }
            grava_byte(code, &i, 0xE8);   /*call rel32*/
            grava_int32(code, &i, function_start[num_func] - (i + 4));
            guardaVar(code, &i, var);
        }
        else if (sscanf(linha, "v%d = %19s %c %19s", &var, a, &op, b) == 4)
        {
            carrega_eax(code, &i, le_op(a));
            aplica_op(code, &i, op, le_op(b));
            guardaVar(code, &i, var);
        }
    }
}