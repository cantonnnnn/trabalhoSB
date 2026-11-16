/* Igual ao seu main.c, mas recebe o arquivo e o argumento pela linha de comando:
   gcc -Wall -Wa,--execstack -o main_args main_args.c gera_codigo.c
   ./main_args testes_txt/enunciado_3_fatorial.txt 5 */
#include <stdio.h>
#include <stdlib.h>
#include "gera_codigo.h"

int main(int argc, char *argv[])
{
    FILE *fp;
    unsigned char code[500];
    funcp funcLBS;
    int resultado;

    if (argc < 3)
    {
        printf("uso: %s arquivo.txt argumento\n", argv[0]);
        return 1;
    }
    fp = fopen(argv[1], "r");
    if (fp == NULL)
    {
        printf("Erro ao abrir arquivo");
        return 1;
    }
    gera_codigo(fp, code, &funcLBS);
    if (funcLBS == NULL)
    {
        printf("Erro na geracao\n");
        return 1;
    }
    resultado = funcLBS(atoi(argv[2]));
    printf("Resultado: %d\n", resultado);
    fclose(fp);
    return 0;
}
