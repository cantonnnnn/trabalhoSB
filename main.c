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