/* main de teste: ./prog_teste arquivo.lbs arg1 arg2 ...
   Gera o codigo do arquivo LBS e imprime f(arg) para cada argumento. */
#include <stdio.h>
#include <stdlib.h>
#include "gera_codigo.h"

int main(int argc, char *argv[])
{
    FILE *fp;
    unsigned char code[4000];
    funcp f;
    int k;

    if (argc < 2) { fprintf(stderr, "uso: %s arquivo.lbs [args...]\n", argv[0]); return 2; }
    fp = fopen(argv[1], "r");
    if (fp == NULL) { perror("fopen"); return 2; }
    gera_codigo(fp, code, &f);
    fclose(fp);
    if (f == NULL) { printf("Erro na geracao\n"); return 1; }
    for (k = 2; k < argc; k++)
        printf("%d\n", f(atoi(argv[k])));
    return 0;
}
