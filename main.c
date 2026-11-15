#include <stdio.h>
#include <stdlib.h>
#include "gera_codigo.h"

int main(int argc, char *argv[]) {
    FILE *fp;
    unsigned char code[500];
    funcp funcLBS;

    if (argc < 3) {
        printf("uso: %s arquivo.lbs argumento\n", argv[0]);
        return 1;
    }
    fp = fopen(argv[1], "r");
    if (fp == NULL) { perror("fopen"); return 1; }

    gera_codigo(fp, code, &funcLBS);
    fclose(fp);

    if (funcLBS == NULL) { printf("Erro na geracao\n"); return 1; }
    printf("%d\n", funcLBS(atoi(argv[2])));
    return 0;
}